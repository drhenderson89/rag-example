"""
Model Handler for Ollama LLM interactions
"""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_ollama.chat_models import ChatOllama
import logging

logger = logging.getLogger(__name__)


class ModelHandler:
    def __init__(self, model_name, ollama_address, config):
        self.model_name = model_name
        self.ollama_address = ollama_address
        self.config = config
        
        self.model = self.load_model()
        system_prompt = config["llm_options"]["system_prompt"]
        if self.model:
            try:
                self.model.invoke([SystemMessage(system_prompt)])
            except Exception as e:
                logger.warning(f"Could not send initial system prompt: {e}")
        
        self.prompt_template = PromptTemplate(
            input_variables=["context", "user_input"],
            template="""Use the following context to answer the question. 
                Context: {context}
                Question: {user_input}
            """
        )
    
    def load_model(self):
        """Load the Ollama model"""
        try:
            model = ChatOllama(
                model=self.model_name,
                base_url=self.ollama_address,
                temperature=self.config["llm_options"]["temperature"],
                num_predict=self.config["llm_options"]["tokens_to_generate"],
            )
            logger.info(f"Loaded model: {self.model_name}")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None

    def combine_context(self, related_docs):
        """Combine the contents of related document parts"""
        context = ""
        for result in related_docs:
            doc = result[0]
            context += doc.page_content + "\n"
        return context

    def get_response(self, user_input, related_docs=None, use_rag=False):
        """Get response from the model with or without RAG context"""
        if not self.model:
            return "Model not loaded. Please check Ollama connection."
        
        try:
            if use_rag and related_docs:
                context = self.combine_context(related_docs)
                prompt = self.prompt_template.format(context=context, user_input=user_input)
                response = self.model.invoke([HumanMessage(prompt)])
            else:
                response = self.model.invoke([HumanMessage(user_input)])
            return response.content
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return f"Error: {str(e)}"
