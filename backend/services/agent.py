import os
import logging
from typing import List, Generator
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class AgenticTutor:
    def __init__(self, course_id: int):
        self.course_id = course_id
        # We configure DeepSeek Chat / OpenAI as the reasoning engine for the agent
        # We are using LangChain's generic ChatOpenAI
        
        # Determine the model. In the project plan, we recommended deepseek-r1:14b or gpt-4o.
        self.model_name = os.getenv("LLM_MODEL", "gpt-4o-mini") 
        self.api_key = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.api_base = os.getenv("LLM_API_BASE", None) 
        
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.api_base,
            temperature=0.3,
            streaming=True
        )
            
        self.doc_processor = DocumentProcessor()

    def _retrieve_context(self, query: str) -> tuple[str, list]:
        """
        Retrieves relevant RAG context from ChromaDB and returns 
        the fused string context alongside the citation metadata.
        """
        results = self.doc_processor.similarity_search(query, self.course_id, top_k=3)
        
        if not results:
            return "No relevant course material found.", []
            
        context_parts = []
        citations = []
        
        for i, res in enumerate(results):
            content = res["content"]
            source = res["metadata"].get("filename", f"source_{i+1}")
            context_parts.append(f"[Document {i+1} - {source}]:\n{content}")
            citations.append({"id": i+1, "source": source, "content_preview": content[:100]})
            
        return "\n\n".join(context_parts), citations

    def stream_chat(self, history: List[dict], user_message: str) -> Generator[str, None, None]:
        """
        ReAct style prompt injection: we give the model RAG context to reason over.
        Returns a streaming generator.
        """
        context_str, citations = self._retrieve_context(user_message)
        
        system_prompt = f"""
        你是一位大学课程的 AI 助教。
        请仔细阅读以下来源于课程讲义/教材的资料片段，来回答学生的问题。
        如果你引用的了资料的内容，请务必在回答中通过 [编号] 进行标注（Citations），例如 [1]。
        如果资料中没有直接答案，请运用教育学原则“苏格拉底式提问”引导学生思考，而不是盲目给出可能错误的推论。
        决不允许产生幻觉（Hallucinations）。

        === 检索到的参考课程资料 ===
        {context_str}
        =========================
        """
        
        messages = [SystemMessage(content=system_prompt)]
        
        # Append historical context (last 6 turns limit is recommended)
        for msg in history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                # Note: For LangChain we simulate assistant with AIMessage, here we just use SystemMessage or standard.
                # For simplicity in MVP, we format it.
                messages.append(SystemMessage(content=f"Assistant Past Reply: {msg['content']}"))
                
        messages.append(HumanMessage(content=user_message))
        
        # Start streaming response
        try:
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    yield chunk.content
                    
            # Yield citations at the very end in a special format or markdown
            if citations:
                yield "\n\n**资料引用来源 (Citations):**\n"
                for cit in citations:
                    yield f"- [{cit['id']}] {cit['source']}\n"
                    
        except Exception as e:
            logger.error(f"Agent stream error: {e}")
            yield f"\n[System Error: {str(e)}]"
