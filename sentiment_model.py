"""
Sentiment Analysis Inference Module
Supports both Naive Bayes (current) and IndoBERT (future)
"""

import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SentimentPrediction:
    """Sentiment prediction result"""
    text: str
    label: str
    confidence: float
    scores: Dict[str, float]
    model_name: str


class SentimentModel:
    """
    Base sentiment analysis model
    Supports both Naive Bayes and IndoBERT
    """
    
    def __init__(self, model_path: Optional[Path] = None, model_type: str = "naive_bayes"):
        """
        Initialize sentiment model
        
        Args:
            model_path: Path to trained model
            model_type: "naive_bayes" or "indobert"
        """
        self.model_type = model_type
        self.model = None
        self.label_map = {0: "Negative", 1: "Neutral", 2: "Positive"}
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}
        
        if model_path:
            self.load_model(model_path)
        else:
            self._load_default_model()
    
    def _load_default_model(self):
        """Load default Naive Bayes model from artifacts"""
        project_root = Path(__file__).parent
        nb_path = project_root / "artifacts" / "naive_bayes_pipeline.joblib"
        
        if nb_path.exists():
            logger.info(f"Loading Naive Bayes from {nb_path}")
            self.model = joblib.load(nb_path)
            self.model_type = "naive_bayes"
            logger.info("✓ Naive Bayes model loaded")
        else:
            logger.warning(f"⚠ Default model not found at {nb_path}")
    
    def load_model(self, model_path: Path):
        """Load trained model from disk"""
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        if self.model_type == "naive_bayes":
            self.model = joblib.load(model_path)
            logger.info(f"✓ Loaded Naive Bayes model from {model_path}")
        
        elif self.model_type == "indobert":
            try:
                from transformers import pipeline
                self.model = pipeline(
                    "text-classification",
                    model=str(model_path),
                    device=0  # GPU if available
                )
                logger.info(f"✓ Loaded IndoBERT model from {model_path}")
            except Exception as e:
                logger.error(f"❌ Failed to load IndoBERT: {e}")
                raise
    
    def predict_single(self, text: str) -> SentimentPrediction:
        """Predict sentiment for single text"""
        if not text or not self.model:
            return None
        
        if self.model_type == "naive_bayes":
            return self._predict_naive_bayes(text)
        elif self.model_type == "indobert":
            return self._predict_indobert(text)
    
    def _predict_naive_bayes(self, text: str) -> SentimentPrediction:
        """Predict using Naive Bayes"""
        try:
            # Get prediction
            pred_label = self.model.predict([text])[0]
            
            # Get confidence scores
            pred_proba = self.model.predict_proba([text])[0]
            
            # Find confidence for predicted label
            confidence = float(pred_proba[pred_label])
            
            # Create score dict
            scores = {
                self.label_map[i]: float(prob)
                for i, prob in enumerate(pred_proba)
            }
            
            # Return result
            return SentimentPrediction(
                text=text,
                label=self.label_map[pred_label],
                confidence=confidence,
                scores=scores,
                model_name="Naive Bayes"
            )
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return None
    
    def _predict_indobert(self, text: str) -> SentimentPrediction:
        """Predict using IndoBERT"""
        try:
            result = self.model(text, truncation=True, max_length=512)
            
            label = result[0]['label']
            confidence = result[0]['score']
            
            return SentimentPrediction(
                text=text,
                label=label.capitalize(),
                confidence=confidence,
                scores={label.capitalize(): confidence},
                model_name="IndoBERT"
            )
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return None
    
    def predict_batch(self, texts: List[str], 
                     batch_size: int = 32,
                     return_dataframe: bool = True) -> pd.DataFrame:
        """
        Predict sentiment for batch of texts
        
        Args:
            texts: List of texts to classify
            batch_size: Batch size for processing
            return_dataframe: Return as DataFrame
        
        Returns:
            DataFrame with predictions or list of SentimentPrediction
        """
        if not texts or not self.model:
            return pd.DataFrame() if return_dataframe else []
        
        logger.info(f"Predicting sentiment for {len(texts)} texts...")
        
        predictions = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            for text in batch:
                pred = self.predict_single(text)
                if pred:
                    predictions.append(pred)
            
            # Progress log
            if (i + batch_size) % (batch_size * 10) == 0:
                logger.info(f"  Processed {i + batch_size}/{len(texts)}")
        
        logger.info(f"✓ Completed {len(predictions)} predictions")
        
        if return_dataframe:
            return self._predictions_to_dataframe(predictions)
        else:
            return predictions
    
    def _predictions_to_dataframe(self, predictions: List[SentimentPrediction]) -> pd.DataFrame:
        """Convert predictions to DataFrame"""
        data = []
        
        for pred in predictions:
            row = {
                'text': pred.text,
                'sentiment': pred.label,
                'confidence': pred.confidence,
                'model': pred.model_name,
            }
            
            # Add scores for each sentiment
            for sentiment, score in pred.scores.items():
                row[f'score_{sentiment.lower()}'] = score
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'model_type': self.model_type,
            'labels': list(self.label_map.values()),
            'num_classes': len(self.label_map),
            'loaded': self.model is not None,
        }


class EnsembleSentimentModel:
    """
    Ensemble of multiple sentiment models
    Combines Naive Bayes + IndoBERT for robust predictions
    """
    
    def __init__(self, 
                 nb_model_path: Optional[Path] = None,
                 indobert_model_path: Optional[Path] = None,
                 weights: Dict[str, float] = None):
        """
        Initialize ensemble with multiple models
        
        Args:
            nb_model_path: Path to Naive Bayes model
            indobert_model_path: Path to IndoBERT model
            weights: Model weights for voting (sum should = 1.0)
        """
        self.models = {}
        self.weights = weights or {
            'naive_bayes': 0.4,
            'indobert': 0.6
        }
        
        # Load Naive Bayes
        if nb_model_path:
            try:
                self.models['naive_bayes'] = SentimentModel(nb_model_path, "naive_bayes")
                logger.info("✓ Naive Bayes loaded for ensemble")
            except Exception as e:
                logger.warning(f"⚠ Could not load Naive Bayes: {e}")
        
        # Load IndoBERT
        if indobert_model_path:
            try:
                self.models['indobert'] = SentimentModel(indobert_model_path, "indobert")
                logger.info("✓ IndoBERT loaded for ensemble")
            except Exception as e:
                logger.warning(f"⚠ Could not load IndoBERT: {e}")
        
        if not self.models:
            logger.warning("⚠ No models loaded for ensemble")
    
    def predict_single(self, text: str) -> SentimentPrediction:
        """Ensemble prediction for single text"""
        if not self.models:
            return None
        
        predictions = {}
        scores = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
        
        # Get predictions from each model
        for model_name, model in self.models.items():
            pred = model.predict_single(text)
            if pred:
                predictions[model_name] = pred
                weight = self.weights.get(model_name, 1.0)
                
                # Accumulate weighted scores
                for sentiment, score in pred.scores.items():
                    scores[sentiment] += score * weight
        
        # Get highest scoring sentiment
        final_sentiment = max(scores, key=scores.get)
        final_confidence = scores[final_sentiment]
        
        return SentimentPrediction(
            text=text,
            label=final_sentiment,
            confidence=final_confidence,
            scores=scores,
            model_name="Ensemble"
        )
    
    def predict_batch(self, texts: List[str], return_dataframe: bool = True):
        """Batch ensemble predictions"""
        logger.info(f"Ensemble predicting {len(texts)} texts...")
        
        predictions = [self.predict_single(text) for text in texts]
        
        if return_dataframe:
            data = []
            for pred in predictions:
                data.append({
                    'text': pred.text,
                    'sentiment': pred.label,
                    'confidence': pred.confidence,
                    'score_positive': pred.scores.get('Positive', 0),
                    'score_neutral': pred.scores.get('Neutral', 0),
                    'score_negative': pred.scores.get('Negative', 0),
                    'model': pred.model_name,
                })
            return pd.DataFrame(data)
        else:
            return predictions


# Convenience functions
def load_sentiment_model(model_type: str = "naive_bayes",
                        model_path: Optional[Path] = None) -> SentimentModel:
    """Load sentiment model"""
    return SentimentModel(model_path, model_type)


def predict_sentiment(text: str, model: SentimentModel = None) -> Dict:
    """Quick sentiment prediction"""
    if model is None:
        model = SentimentModel()
    
    pred = model.predict_single(text)
    
    if pred:
        return {
            'text': pred.text,
            'sentiment': pred.label,
            'confidence': float(pred.confidence),
            'scores': {k: float(v) for k, v in pred.scores.items()},
        }
    return None


# Example usage
if __name__ == "__main__":
    # Initialize model (uses Naive Bayes by default)
    model = SentimentModel()
    
    print("=" * 60)
    print("SENTIMENT ANALYSIS - DEMO")
    print("=" * 60)
    
    # Test samples
    samples = [
        "keren banget kontennya! suka sekali",
        "jelek bet, sangat mengecewakan",
        "biasa aja, tidak terlalu bagus",
        "amazing! love this content",
        "absolutely terrible, worst ever",
    ]
    
    # Predict
    for text in samples:
        result = predict_sentiment(text, model)
        if result:
            print(f"\nText: {text}")
            print(f"Sentiment: {result['sentiment']}")
            print(f"Confidence: {result['confidence']:.2%}")
    
    print("\n" + "=" * 60)
    print("Model Info:")
    print(model.get_model_info())
    print("=" * 60)
