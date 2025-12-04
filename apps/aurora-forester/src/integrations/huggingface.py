"""
Aurora Forester - HuggingFace Integration
Access to HuggingFace models for embeddings, inference, and fine-tuning.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import os
import json
from pathlib import Path

# Note: These imports require huggingface_hub package
# from huggingface_hub import HfApi, InferenceClient
# from sentence_transformers import SentenceTransformer


@dataclass
class ModelInfo:
    """Information about a HuggingFace model."""
    model_id: str
    task: str
    downloads: int = 0
    likes: int = 0
    description: str = ""


class AuroraHuggingFace:
    """
    Aurora's HuggingFace integration.
    Provides access to models for embeddings, inference, and learning.
    """

    # Recommended models for Aurora's use cases
    RECOMMENDED_MODELS = {
        "embeddings": {
            "default": "sentence-transformers/all-MiniLM-L6-v2",
            "multilingual": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "large": "sentence-transformers/all-mpnet-base-v2",
        },
        "sentiment": {
            "default": "cardiffnlp/twitter-roberta-base-sentiment-latest",
            "multilingual": "nlptown/bert-base-multilingual-uncased-sentiment",
        },
        "classification": {
            "zero_shot": "facebook/bart-large-mnli",
            "intent": "MoritzLaworker/intent-classifier-v1",
        },
        "summarization": {
            "default": "facebook/bart-large-cnn",
            "dialogue": "philschmid/bart-large-cnn-samsum",
        },
        "question_answering": {
            "default": "deepset/roberta-base-squad2",
            "large": "deepset/roberta-large-squad2",
        }
    }

    def __init__(self, token: Optional[str] = None):
        """
        Initialize HuggingFace integration.

        Args:
            token: HuggingFace API token. If not provided, will try to load
                   from HUGGINGFACE_TOKEN env var or secure storage.
        """
        self.token = token or self._load_token()
        self._api = None
        self._inference_client = None
        self._embedding_model = None

    def _load_token(self) -> Optional[str]:
        """Load token from environment or secure storage."""
        # Try environment variable
        token = os.environ.get("HUGGINGFACE_TOKEN")
        if token:
            return token

        # Try secure storage
        secure_path = Path.home() / ".aurora-forester" / "secrets" / "huggingface_token"
        if secure_path.exists():
            return secure_path.read_text().strip()

        return None

    @property
    def api(self):
        """Get or create the HuggingFace API client."""
        if self._api is None:
            # from huggingface_hub import HfApi
            # self._api = HfApi(token=self.token)
            pass
        return self._api

    @property
    def inference_client(self):
        """Get or create the inference client."""
        if self._inference_client is None:
            # from huggingface_hub import InferenceClient
            # self._inference_client = InferenceClient(token=self.token)
            pass
        return self._inference_client

    def save_token(self, token: str):
        """Securely save the HuggingFace token."""
        secrets_dir = Path.home() / ".aurora-forester" / "secrets"
        secrets_dir.mkdir(parents=True, exist_ok=True)

        token_file = secrets_dir / "huggingface_token"
        token_file.write_text(token)
        os.chmod(token_file, 0o600)

        self.token = token
        self._api = None
        self._inference_client = None

    def search_models(
        self,
        query: str,
        task: Optional[str] = None,
        limit: int = 10
    ) -> List[ModelInfo]:
        """
        Search for models on HuggingFace Hub.

        Args:
            query: Search query
            task: Optional task filter (e.g., "text-classification")
            limit: Maximum number of results
        """
        # Placeholder - requires huggingface_hub
        # models = self.api.list_models(
        #     search=query,
        #     filter=task,
        #     limit=limit,
        #     sort="downloads",
        #     direction=-1
        # )
        # return [ModelInfo(
        #     model_id=m.modelId,
        #     task=m.pipeline_tag or "unknown",
        #     downloads=m.downloads or 0,
        #     likes=m.likes or 0,
        #     description=m.description or ""
        # ) for m in models]

        return []

    def get_recommended_model(self, use_case: str, variant: str = "default") -> Optional[str]:
        """Get a recommended model for a specific use case."""
        category = self.RECOMMENDED_MODELS.get(use_case, {})
        return category.get(variant)

    async def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed
            model: Model to use (defaults to recommended embedding model)

        Returns:
            List of embedding vectors
        """
        model = model or self.get_recommended_model("embeddings", "default")

        # Placeholder - requires sentence_transformers or inference API
        # Option 1: Local model
        # if self._embedding_model is None:
        #     self._embedding_model = SentenceTransformer(model)
        # return self._embedding_model.encode(texts).tolist()

        # Option 2: Inference API
        # return await self.inference_client.feature_extraction(
        #     texts,
        #     model=model
        # )

        # Return placeholder embeddings (1536 dimensions to match OpenAI)
        return [[0.0] * 1536 for _ in texts]

    async def classify_intent(
        self,
        text: str,
        candidate_labels: List[str]
    ) -> Dict[str, float]:
        """
        Classify the intent of text using zero-shot classification.

        Args:
            text: Text to classify
            candidate_labels: Possible intent labels

        Returns:
            Dictionary of label -> confidence score
        """
        model = self.get_recommended_model("classification", "zero_shot")

        # Placeholder - requires inference API
        # result = await self.inference_client.zero_shot_classification(
        #     text,
        #     candidate_labels,
        #     model=model
        # )
        # return dict(zip(result["labels"], result["scores"]))

        return {label: 0.0 for label in candidate_labels}

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of text.

        Returns:
            Dictionary with sentiment label and confidence
        """
        model = self.get_recommended_model("sentiment", "default")

        # Placeholder
        # result = await self.inference_client.text_classification(
        #     text,
        #     model=model
        # )
        # return result[0]

        return {"label": "neutral", "score": 0.5}

    async def summarize(self, text: str, max_length: int = 150) -> str:
        """
        Summarize a piece of text.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary

        Returns:
            Summary text
        """
        model = self.get_recommended_model("summarization", "default")

        # Placeholder
        # result = await self.inference_client.summarization(
        #     text,
        #     model=model,
        #     parameters={"max_length": max_length}
        # )
        # return result["summary_text"]

        return text[:max_length] + "..." if len(text) > max_length else text

    async def answer_question(
        self,
        question: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Answer a question given context.

        Args:
            question: The question to answer
            context: Context containing the answer

        Returns:
            Dictionary with answer and confidence
        """
        model = self.get_recommended_model("question_answering", "default")

        # Placeholder
        # result = await self.inference_client.question_answering(
        #     question=question,
        #     context=context,
        #     model=model
        # )
        # return result

        return {"answer": "", "score": 0.0, "start": 0, "end": 0}


class EmbeddingService:
    """
    Service for managing embeddings in Aurora's RAG system.
    """

    def __init__(self, hf: AuroraHuggingFace):
        self.hf = hf
        self.dimension = 1536  # Match pgvector dimension

    async def embed_document(self, content: str, title: Optional[str] = None) -> List[float]:
        """Embed a document for RAG storage."""
        text = f"{title}: {content}" if title else content
        embeddings = await self.hf.generate_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * self.dimension

    async def embed_query(self, query: str) -> List[float]:
        """Embed a query for similarity search."""
        embeddings = await self.hf.generate_embeddings([query])
        return embeddings[0] if embeddings else [0.0] * self.dimension

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed a batch of texts efficiently."""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.hf.generate_embeddings(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings


# ============================================
# LEARNING & FINE-TUNING
# ============================================

class AuroraLearningHub:
    """
    Aurora's learning capabilities via HuggingFace.
    Tracks what models might benefit from fine-tuning based on usage.
    """

    def __init__(self, hf: AuroraHuggingFace):
        self.hf = hf
        self.usage_log: List[Dict[str, Any]] = []
        self.feedback_log: List[Dict[str, Any]] = []

    def log_usage(
        self,
        task: str,
        model: str,
        input_text: str,
        output: Any,
        success: bool = True
    ):
        """Log model usage for learning."""
        self.usage_log.append({
            "task": task,
            "model": model,
            "input_preview": input_text[:100],
            "success": success,
            "timestamp": str(__import__("datetime").datetime.now())
        })

    def log_feedback(
        self,
        task: str,
        model: str,
        input_text: str,
        output: Any,
        feedback: str,  # positive, negative, correction
        correction: Optional[str] = None
    ):
        """Log feedback for potential fine-tuning."""
        self.feedback_log.append({
            "task": task,
            "model": model,
            "input_text": input_text,
            "output": str(output),
            "feedback": feedback,
            "correction": correction,
            "timestamp": str(__import__("datetime").datetime.now())
        })

    def get_fine_tuning_candidates(self) -> List[Dict[str, Any]]:
        """
        Identify models that might benefit from fine-tuning
        based on negative feedback patterns.
        """
        from collections import Counter

        negative_by_model = Counter()
        for entry in self.feedback_log:
            if entry["feedback"] == "negative":
                negative_by_model[entry["model"]] += 1

        candidates = []
        for model, count in negative_by_model.most_common():
            if count >= 5:  # Threshold for considering fine-tuning
                candidates.append({
                    "model": model,
                    "negative_feedback_count": count,
                    "recommendation": "Consider fine-tuning or switching models"
                })

        return candidates

    def export_training_data(self, task: str) -> List[Dict[str, str]]:
        """
        Export feedback data for fine-tuning.
        Only includes entries with corrections.
        """
        training_data = []

        for entry in self.feedback_log:
            if entry["task"] == task and entry.get("correction"):
                training_data.append({
                    "input": entry["input_text"],
                    "output": entry["correction"]
                })

        return training_data


# ============================================
# SINGLETON INSTANCES
# ============================================

_huggingface: Optional[AuroraHuggingFace] = None
_embedding_service: Optional[EmbeddingService] = None
_learning_hub: Optional[AuroraLearningHub] = None


def get_huggingface() -> AuroraHuggingFace:
    """Get the singleton HuggingFace client."""
    global _huggingface
    if _huggingface is None:
        _huggingface = AuroraHuggingFace()
    return _huggingface


def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(get_huggingface())
    return _embedding_service


def get_learning_hub() -> AuroraLearningHub:
    """Get the singleton learning hub."""
    global _learning_hub
    if _learning_hub is None:
        _learning_hub = AuroraLearningHub(get_huggingface())
    return _learning_hub
