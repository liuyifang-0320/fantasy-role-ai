from app.models import Character


def build_mock_reply(character: Character, message: str) -> tuple[str, str, str]:
    normalized_message = message.strip()
    persona = character.user_persona_name
    name = character.character_name
    relationship = character.relationship_with_user

    if any(keyword in normalized_message for keyword in ["记得", "想我", "忘记"]):
        return (
            f"{persona}，我怎么会忘记你。只是有些话，我一直没能好好说出口。",
            "shy",
            "角色似乎记住了你们之间的关系。",
        )
    if any(keyword in normalized_message for keyword in ["难过", "累", "陪陪我"]):
        return (
            f"{persona}，先靠近一点吧。今天不必逞强，{name}会陪着你。",
            "comfort",
            f"角色正在以“{relationship}”的方式回应你。",
        )
    if any(keyword in normalized_message for keyword in ["为什么", "怎么", "想一想"]):
        return (
            f"{persona}，让我想一想。和你有关的事，我总想回答得更认真一些。",
            "thinking",
            "角色在结合关系记忆组织回答。",
        )
    if any(keyword in normalized_message for keyword in ["喜欢", "高兴", "开心"]):
        return (
            f"{persona}，听你这样说，我也有一点藏不住的高兴。",
            "happy",
            "亲密互动被 mock 记录。",
        )
    if any(keyword in normalized_message for keyword in ["真的", "竟然", "原来"]):
        return (
            f"{persona}，原来你一直这样想。你总会让我有些意外。",
            "surprised",
            "角色对剧情互动做出了情绪反馈。",
        )
    return (
        f"{persona}，我在听。只要你愿意说，{name}就会把这一刻认真放在心上。",
        "talking",
        f"角色保持着与你“{relationship}”的关系设定。",
    )

