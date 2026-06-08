from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.survey_loader import survey_manager, Orchestrator
from app.services.routing import (
    compute_next_state,
    compute_go_back_state,
    compute_multi_select_state,
    compute_start_route,
    resolve_next_route,
)
from app.services import survey_repository as repo
from app.services import survey_messages as messages
from app.config import GO_BACK_KEYWORD, CONFIRM_KEYWORD


def _walk_total(survey, start_route_id: str, payload: dict = None) -> int:
    """Walk the survey from start_route_id, resolving Orchestrator branches from the actual payload.

    When payload is empty (session just started and the branching question hasn't been answered yet),
    unresolved Orchestrators fall through to their `default`; the total grows correctly once
    the branching answer lands in payload on the next call.
    """
    payload = payload or {}
    total = 0
    visited = set()
    route_id = start_route_id
    while route_id and route_id not in visited:
        visited.add(route_id)
        route = survey.routes.get(route_id)
        if not route:
            break
        total += len(route.questions)
        next_spec = route.next
        if next_spec is None:
            break
        elif isinstance(next_spec, str):
            route_id = next_spec
        elif isinstance(next_spec, Orchestrator):
            route_id = resolve_next_route(next_spec, payload)
            if route_id is None:
                break
        else:
            break
    return total


def _global_step(survey, route_history: list, current_step: int) -> int:
    """Compute absolute question index across all completed routes (route_history) plus current_step."""
    return sum(
        len(survey.routes[entry["route_id"]].questions)
        for entry in (route_history or [])
        if entry["route_id"] in survey.routes
    ) + current_step


async def start_survey_session(user_id: str, survey_version: str, reply_token: str, line_bot_api, db: AsyncSession):
    user = await repo.get_or_create_user(db, user_id)
    await repo.clear_session(db, user_id)

    survey = survey_manager.get_survey(survey_version)
    start_route_id = compute_start_route(survey, user.has_completed_profile)

    await repo.create_session(db, user_id, survey_version, start_route_id)

    # Send the first question of the starting route (no go-back on the first question)
    first_question_id = survey.routes[start_route_id].questions[0]
    first_question = survey_manager.get_question(survey_version, first_question_id)
    if first_question:
        total = _walk_total(survey, start_route_id, {})
        await messages.send_question(reply_token, first_question, line_bot_api, show_go_back=False, step=0, total=total)


async def process_survey_answer(user_id: str, answer_data, reply_token: str, line_bot_api, db: AsyncSession):
    # 1. Load active session
    active_session = await repo.load_session(db, user_id)
    if not active_session:
        await messages.send_text(reply_token, "กรุณากดปุ่มเมนูเพื่อเริ่มแบบสำรวจครับ", line_bot_api)
        return

    survey_version = active_session.survey_version
    survey = survey_manager.get_survey(survey_version)

    # 2. Handle go-back before touching the payload
    if answer_data == GO_BACK_KEYWORD:
        go_back = compute_go_back_state(
            active_session.current_route_id,
            active_session.current_step,
            active_session.route_history or [],
            survey,
        )
        if go_back["action"] == "at_beginning":
            return

        # Clear the answer for the question we're returning to so the user re-answers it
        payload = (active_session.payload or {}).copy()
        payload.pop(go_back["question_id"], None)
        active_session.payload = payload
        active_session.current_route_id = go_back["route_id"]
        active_session.current_step = go_back["step"]
        new_history = list(go_back["route_history"]) if "route_history" in go_back else (active_session.route_history or [])
        active_session.route_history = new_history
        # Compute progress BEFORE commit — committing expires ORM attributes (expire_on_commit)
        # and reading them back would trigger a lazy DB load outside the async greenlet.
        total = _walk_total(survey, survey.onstart, payload)
        gstep = _global_step(survey, new_history, go_back["step"])
        await repo.save_session(db)

        prev_question = survey_manager.get_question(survey_version, go_back["question_id"])
        is_first = (go_back["route_id"] == survey.onstart and go_back["step"] == 0)
        await messages.send_question(reply_token, prev_question, line_bot_api, show_go_back=not is_first, step=gstep, total=total)
        return

    # 3. Identify the question the user just answered
    current_route = survey.routes[active_session.current_route_id]
    current_question_id = current_route.questions[active_session.current_step]
    current_question = survey_manager.get_question(survey_version, current_question_id)

    # 4. Handle multi_select accumulation
    if current_question and current_question.type == "multi_select":
        pending_all = (active_session.pending_multi_select or {}).copy()
        pending_this = pending_all.get(current_question_id, [])
        ms_result = compute_multi_select_state(
            pending=pending_this,
            new_answer=answer_data,
            max_selections=current_question.max_selections or 99,
            confirm_keyword=CONFIRM_KEYWORD,
        )

        if ms_result["action"] == "ignore":
            return

        if ms_result["action"] == "accumulate":
            pending_all[current_question_id] = ms_result["pending"]
            active_session.pending_multi_select = pending_all
            # Capture progress inputs BEFORE commit — commit expires ORM attributes and
            # reading them back would trigger a lazy DB load outside the async greenlet.
            max_sel = current_question.max_selections or 99
            total = _walk_total(survey, survey.onstart, active_session.payload or {})
            gstep = _global_step(survey, active_session.route_history or [], active_session.current_step)
            await repo.save_session(db)
            await messages.send_question(
                reply_token, current_question, line_bot_api,
                show_go_back=True,
                multi_select_pending=ms_result["pending"],
                multi_select_max=max_sel,
                step=gstep,
                total=total,
            )
            return

        # action == "confirm" — save final answers and fall through to routing
        pending_all.pop(current_question_id, None)
        active_session.pending_multi_select = pending_all
        answer_data = ms_result["answers"]

    # 5. Handle image answer — store proxy URL instead of downloading
    if isinstance(answer_data, dict) and "image_id" in answer_data:
        answer_data["image_url"] = f"/api/dashboard/image/{answer_data['image_id']}"

    # 6. Save answer into payload (copy() so SQLAlchemy detects the change)
    payload = active_session.payload.copy() if active_session.payload else {}
    payload[current_question_id] = answer_data
    active_session.payload = payload

    # 7. Ask the routing engine where to go next
    result = compute_next_state(
        current_route_id=active_session.current_route_id,
        current_step=active_session.current_step,
        route_history=active_session.route_history or [],
        payload=payload,
        survey=survey,
    )

    # 8. Act on the routing decision
    if result["action"] == "next_question":
        active_session.current_route_id = result["current_route_id"]
        active_session.current_step = result["current_step"]
        active_session.route_history = list(result["route_history"])
        await repo.save_session(db)
        next_question = survey_manager.get_question(survey_version, result["next_question_id"])
        total = _walk_total(survey, survey.onstart, payload)
        gstep = _global_step(survey, result["route_history"], result["current_step"])
        await messages.send_question(reply_token, next_question, line_bot_api, show_go_back=True, step=gstep, total=total)

    elif result["action"] == "next_route":
        # If we just finished the profile route, mark the user as profiled
        if active_session.current_route_id == survey.onstart:
            await repo.mark_profile_completed(db, user_id)

        active_session.current_route_id = result["current_route_id"]
        active_session.current_step = result["current_step"]
        active_session.route_history = list(result["route_history"])
        await repo.save_session(db)
        next_question = survey_manager.get_question(survey_version, result["next_question_id"])
        total = _walk_total(survey, survey.onstart, payload)
        gstep = _global_step(survey, result["route_history"], result["current_step"])
        await messages.send_question(reply_token, next_question, line_bot_api, show_go_back=True, step=gstep, total=total)

    elif result["action"] == "complete":
        await repo.finalize_report(db, active_session)
        await messages.send_text(reply_token, "ขอบคุณที่ร่วมรายงานข้อมูลครับ", line_bot_api)
