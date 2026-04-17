from groq import AsyncGroq
from config import GROQ_API_KEY

client = AsyncGroq(api_key=GROQ_API_KEY)

async def ask_ai(system_prompt: str, user_message: str, history: list = None) -> str:
    messages = []
    
    if history:
        messages.extend(history[-6:])  # последние 6 сообщений контекста
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}] + messages,
            max_tokens=800,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка AI: {str(e)}\n\nПопробуй ещё раз."
