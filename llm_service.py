import openai
from dotenv import load_dotenv
import os

class OpenAIService:
    def __init__(self):
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        self.client = openai.OpenAI(api_key=self.openai_api_key)

    def get_qa_response(self, prompt: str, model: str = "gpt-4o", temperature: float = 0.5, max_tokens: int = 700) -> str:
        """
        OpenAI API를 사용하여 질문에 대한 답변을 생성합니다.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except openai.APIError as e:
            return f"❌ OpenAI API 오류: {e}"
        except Exception as e:
            return f"❌ AI 답변 생성 중 오류 발생: {e}"