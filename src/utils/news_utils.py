import requests
import os
from dotenv import load_dotenv
import time
from mistralai import Mistral
from openai import OpenAI

# Load environment variables first
load_dotenv()

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')


def ai_call(prompt: str, task: str = "general", use_reasoning: bool = False) -> str:
    """
    เรียกใช้ AI API โดยลองใช้ DeepSeek ก่อน ถ้าไม่สำเร็จให้ใช้ Mistral เป็นทางเลือกสำรอง
    
    Args:
        prompt (str): คำถามหรือคำสั่งที่ต้องการส่งให้ AI
        task (str): ประเภทของงาน ('translate', 'summarize', 'decision', 'general')
        use_reasoning (bool): ถ้า True จะใช้ deepseek-reasoner สำหรับการวิเคราะห์เชิงลึก
    """
    if use_reasoning:
        # ใช้ deepseek-reasoner สำหรับงานที่ต้องการเหตุผลเชิงลึก
        result = deepseek_reasoner_call(prompt, task)
    else:
        # ใช้ deepseek-chat ปกติ
        result = deepseek_api_call(prompt, task)

    if result and result.startswith("[DeepSeek API error"):
        print("🔄 Falling back to Mistral API...")
        return mistral_api_call(prompt, task)

    return result


def mistral_api_call(prompt: str, task: str = "general") -> str:
    """
    เรียกใช้ Mistral API เป็นทางเลือกสำรอง (ใช้ SDK ทางการ)
    """
    if not MISTRAL_API_KEY:
        return f"[Mistral API error: API key not found]"

    try:
        # Initialize Mistral client
        client = Mistral(api_key=MISTRAL_API_KEY)
        
        # System message based on task type
        system_message = f"Task: {task}"
        
        # Create the chat completion
        response = client.chat.completions.create(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.2
        )
        
        # Extract the response text
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Mistral API error]: {e}")
        return f"[Mistral API error: {e}]"


def deepseek_api_call(prompt: str, task: str = "general") -> str:
    """
    เรียก DeepSeek API โมเดล deepseek-chat (ใช้ SDK OpenAI-compatible)
    task: "translate", "summarize", "decision", "general"
    """
    if not DEEPSEEK_API_KEY:
        return f"[DeepSeek API error: API key not found in environment variables]"

    try:
        # Initialize OpenAI client with DeepSeek base URL
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        
        # Create message payload
        messages = [
            {"role": "system", "content": f"Task: {task}"},
            {"role": "user", "content": prompt}
        ]
        
        # Make the API call
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.2
        )
        
        # Extract and return the response
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[DeepSeek API error]: {e}")
        return f"[DeepSeek API error: {e}]"


def deepseek_reasoner_call(prompt: str, task: str = "general") -> str:
    """
    เรียก DeepSeek API โมเดล deepseek-reasoner สำหรับการวิเคราะห์เชิงลึกที่ต้องการเหตุผลประกอบ
    task: "translate", "summarize", "decision", "general", "sentiment", "strategy"
    
    โมเดลนี้มี reasoning_content ที่แสดงกระบวนการคิดได้ด้วย
    """
    if not DEEPSEEK_API_KEY:
        return f"[DeepSeek API error: API key not found in environment variables]"

    try:
        # Initialize OpenAI client with DeepSeek base URL
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        
        # Create message payload
        messages = [
            {"role": "system", "content": f"Task: {task}. Think step by step before providing your answer."},
            {"role": "user", "content": prompt}
        ]
        
        # Make the API call to deepseek-reasoner model
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages,
            temperature=0.2
        )
        
        # Get both the reasoning and regular content
        reasoning = response.choices[0].message.reasoning_content
        answer = response.choices[0].message.content.strip()
        
        # For debugging/logging (can be removed in production)
        print(f"DeepSeek Reasoning: {reasoning[:100]}...")
        
        # Just return the answer, not the reasoning process
        return answer
    except Exception as e:
        print(f"[DeepSeek Reasoner API error]: {e}")
        return f"[DeepSeek API error: {e}]"


def summarize_text(text: str) -> str:
    """
    สรุปข่าวภาษาอังกฤษด้วย AI API (DeepSeek หรือ Mistral)
    """
    prompt = f"ช่วยสรุปข่าวนี้ให้กระชับ ด้วยประโยคแบบเป็นกันเอง 2 ประโยค:\n{text}"
    return ai_call(prompt, task="summarize")


def sentiment_analysis(text: str) -> str:
    """
    วิเคราะห์ sentiment (Bullish, Bearish, Neutral) ด้วย AI API (DeepSeek หรือ Mistral)
    ใช้ deepseek-reasoner เพื่อการวิเคราะห์เชิงลึกที่มีเหตุผลประกอบ
    """
    prompt = (
        "ช่วยวิเคราะห์ความรู้สึกของข่าวการเงินนี้หน่อย "
        "ตอบแค่คำเดียว: Bullish (เป็นบวก), Bearish (เป็นลบ), หรือ Neutral (เป็นกลาง)\n"
        f"ข้อความ: {text}"
    )
    return ai_call(prompt, task="sentiment", use_reasoning=True)


FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')


def translate_text(text: str) -> str:
    """
    แปลข้อความอังกฤษ→ไทย ด้วย AI API (DeepSeek หรือ Mistral)
    """
    prompt = f"ช่วยแปลข้อความนี้เป็นภาษาไทยนะ ใช้สำนวนที่เป็นธรรมชาติ เข้าใจง่าย:\n{text}"
    return ai_call(prompt, task="translate")


def generate_strategy(news_text: str) -> str:
    """
    สร้าง investment strategy จากข่าวด้วย AI API (DeepSeek หรือ Mistral)
    ใช้ deepseek-reasoner เพื่อการวิเคราะห์และให้คำแนะนำเชิงลึกที่มีเหตุผลประกอบ
    """
    prompt = (
        "จากข่าวการเงินต่อไปนี้ ช่วยสร้างกลยุทธ์การลงทุนที่กระชับหรือข้อมูลเชิงปฏิบัติ "
        "ตอบเป็นภาษาอังกฤษ 2-3 ประโยค และเน้นที่ขั้นตอนที่ปฏิบัติได้จริงหรือจุดยืนในตลาด\n"
        f"ข่าว: {news_text}"
    )
    return ai_call(prompt, task="strategy", use_reasoning=True)


def get_latest_news() -> str | None:
    """ดึงข่าวเศรษฐกิจล่าสุดจาก Finnhub API และแปลเป็นภาษาไทยก่อนส่งออก"""
    if not FINNHUB_API_KEY:
        raise ValueError('Missing FINNHUB_API_KEY in environment variables')

    url = f'https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        news_list = response.json()
        if isinstance(news_list, list) and news_list:
            latest = news_list[0]
            headline = latest.get('headline', 'ไม่มีหัวข้อข่าว')
            summary = latest.get('summary', '')
            news_url = latest.get('url', '')

            # สรุปข่าว (EN/TH)
            summary_en_short = summarize_text(summary)
            summary_th_short = translate_text(summary_en_short)

            # กลยุทธ์จากข่าว
            strategy_en = generate_strategy(summary)
            strategy_th = translate_text(strategy_en)

            # แปล headline และ summary
            headline_th = translate_text(headline)
            summary_th = translate_text(summary)
            news_message = (
                f"📰 ข่าวล่าสุด: {headline_th}\n\n"
                f"🔍 สรุป: {summary_th_short}\n\n"
                f"💡 กลยุทธ์: {strategy_th}\n\n"
                f"📝 เนื้อหาเต็ม: {summary_th}\n\n"
                f"🔗 อ่านต่อ: {news_url}"
            )
            return news_message
        return None
    except Exception as e:
        print(f'Error fetching news: {e}')
        return None
