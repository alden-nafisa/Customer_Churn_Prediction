"""
NLP Preprocessing Pipeline
Combines emoji conversion, slang expansion, and text normalization
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
import unicodedata
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download NLTK data if not present
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPPreprocessor:
    """
    Comprehensive text preprocessing for Indonesian/English YouTube comments
    
    Pipeline:
    1. Remove mentions (@username)
    2. Convert emojis to text
    3. Expand Indonesian slang
    4. Normalize whitespace
    5. Remove special characters (optional)
    6. Lowercase
    """
    
    def __init__(self, 
                 emoji_mapping_file: Optional[Path] = None,
                 slang_mapping_file: Optional[Path] = None,
                 remove_special_chars: bool = False,
                 remove_stopwords: bool = False):
        """
        Initialize preprocessor with emoji and slang mappings
        
        Args:
            emoji_mapping_file: Path to emoji_mappings.json
            slang_mapping_file: Path to slang_dictionary.json
            remove_special_chars: Remove non-alphanumeric characters
            remove_stopwords: Remove Indonesian stopwords
        """
        self.remove_special_chars = remove_special_chars
        self.remove_stopwords = remove_stopwords
        
        # Load emoji mappings
        if emoji_mapping_file is None:
            emoji_mapping_file = Path(__file__).parent / "emoji_mappings.json"
        
        try:
            with open(emoji_mapping_file, 'r', encoding='utf-8') as f:
                self.emoji_map = json.load(f)
            logger.info(f"✓ Loaded {len(self.emoji_map)} emoji mappings")
        except FileNotFoundError:
            logger.warning(f"⚠ Emoji mappings not found at {emoji_mapping_file}")
            self.emoji_map = {}
        
        # Load slang mappings
        if slang_mapping_file is None:
            slang_mapping_file = Path(__file__).parent / "slang_dictionary.json"
        
        try:
            with open(slang_mapping_file, 'r', encoding='utf-8') as f:
                self.slang_map = json.load(f)
            logger.info(f"✓ Loaded {len(self.slang_map)} slang mappings")
        except FileNotFoundError:
            logger.warning(f"⚠ Slang dictionary not found at {slang_mapping_file}")
            self.slang_map = {}
        
        # Load stopwords
        try:
            self.stopwords_id = set(stopwords.words('indonesian'))
            self.stopwords_en = set(stopwords.words('english'))
            logger.info(f"✓ Loaded stopwords (ID: {len(self.stopwords_id)}, EN: {len(self.stopwords_en)})")
        except:
            logger.warning("⚠ Could not load stopwords")
            self.stopwords_id = set()
            self.stopwords_en = set()
        
        self.stats = {
            "mentions_removed": 0,
            "emojis_converted": 0,
            "slang_expanded": 0,
            "special_chars_removed": 0,
            "stopwords_removed": 0,
        }
    
    def remove_mentions(self, text: str) -> str:
        """Remove @username mentions"""
        if not text:
            return text
        
        original_length = len(re.findall(r'@\w+', text))
        text = re.sub(r'@\w+', '', text)
        self.stats["mentions_removed"] += original_length
        return text
    
    def convert_emojis(self, text: str) -> str:
        """Convert emojis to text using mapping"""
        if not text or not self.emoji_map:
            return text
        
        for emoji, translation in self.emoji_map.items():
            if emoji in text:
                text = text.replace(emoji, f" {translation} ")
                self.stats["emojis_converted"] += text.count(emoji)
        
        return text
    
    def expand_slang(self, text: str) -> str:
        """Expand Indonesian slang to full words"""
        if not text or not self.slang_map:
            return text
        
        # Case-insensitive replacement for slang
        words = text.split()
        expanded_words = []
        
        for word in words:
            # Try exact match first
            if word.lower() in self.slang_map:
                expanded_words.append(self.slang_map[word.lower()])
                self.stats["slang_expanded"] += 1
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    def remove_urls(self, text: str) -> str:
        """Remove URLs from text"""
        if not text:
            return text
        return re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace - remove extra spaces, tabs, newlines"""
        if not text:
            return text
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def normalize_characters(self, text: str) -> str:
        """Normalize Unicode characters"""
        if not text:
            return text
        
        # Normalize Unicode (NFD → NFC)
        text = unicodedata.normalize('NFKC', text)
        return text
    
    def remove_special_characters(self, text: str, keep_chars: str = "") -> str:
        """Remove special characters, keeping alphanumeric and specified chars"""
        if not text or not self.remove_special_chars:
            return text
        
        # Keep alphanumeric, spaces, and specified characters
        pattern = f'[^a-zA-Z0-9\\s{re.escape(keep_chars)}]'
        cleaned = re.sub(pattern, '', text)
        
        count = len(text) - len(cleaned)
        if count > 0:
            self.stats["special_chars_removed"] += count
        
        return cleaned
    
    def remove_stopwords_func(self, text: str, language: str = 'indonesian') -> str:
        """Remove stopwords from text"""
        if not text or not self.remove_stopwords:
            return text
        
        try:
            # Tokenize
            words = word_tokenize(text.lower())
            
            # Select stopword set
            stopwords_set = self.stopwords_id if language == 'indonesian' else self.stopwords_en
            
            # Filter
            filtered = [w for w in words if w not in stopwords_set and w.isalpha()]
            
            self.stats["stopwords_removed"] += len(words) - len(filtered)
            
            return ' '.join(filtered)
        except:
            logger.warning("⚠ Stopword removal failed")
            return text
    
    def lowercase(self, text: str) -> str:
        """Convert to lowercase"""
        if not text:
            return text
        return text.lower()
    
    def preprocess(self, text: str, 
                   remove_urls: bool = True,
                   keep_special: bool = True,
                   chain_all: bool = True) -> str:
        """
        Complete preprocessing pipeline
        
        Args:
            text: Raw text to preprocess
            remove_urls: Remove URLs from text
            keep_special: Keep special chars (for sentiment, use True; for pure text, use False)
            chain_all: Apply all transformations in optimal order
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Reset stats for this text
        text_stats = {}
        
        # Optimal pipeline order:
        if chain_all:
            # 1. Remove URLs (often contain emoji and noise)
            if remove_urls:
                text = self.remove_urls(text)
            
            # 2. Remove mentions (@username)
            text = self.remove_mentions(text)
            
            # 3. Convert emojis to text
            text = self.convert_emojis(text)
            
            # 4. Expand slang
            text = self.expand_slang(text)
            
            # 5. Normalize characters (Unicode)
            text = self.normalize_characters(text)
            
            # 6. Normalize whitespace
            text = self.normalize_whitespace(text)
            
            # 7. Lowercase
            text = self.lowercase(text)
            
            # 8. Optional: Remove special characters (careful - affects sentiment!)
            if not keep_special:
                text = self.remove_special_characters(text, keep_chars=".,!?")
            
            # 9. Optional: Remove stopwords
            if self.remove_stopwords:
                text = self.remove_stopwords_func(text)
            
            # 10. Final normalization
            text = self.normalize_whitespace(text)
        
        return text
    
    def preprocess_batch(self, texts: List[str], **kwargs) -> List[str]:
        """Process list of texts efficiently"""
        logger.info(f"Processing {len(texts)} texts...")
        
        # Reset stats
        for key in self.stats:
            self.stats[key] = 0
        
        results = [self.preprocess(text, **kwargs) for text in texts]
        
        logger.info(f"✓ Batch processing complete")
        logger.info(f"  Mentions removed: {self.stats['mentions_removed']}")
        logger.info(f"  Emojis converted: {self.stats['emojis_converted']}")
        logger.info(f"  Slang expanded: {self.stats['slang_expanded']}")
        
        return results
    
    def get_stats(self) -> Dict:
        """Get preprocessing statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        for key in self.stats:
            self.stats[key] = 0


# Convenience function
def preprocess_text(text: str, **kwargs) -> str:
    """Quick preprocessing with default preprocessor"""
    preprocessor = NLPPreprocessor(**kwargs)
    return preprocessor.preprocess(text)


# Example usage
if __name__ == "__main__":
    # Initialize preprocessor
    prep = NLPPreprocessor(
        remove_special_chars=False,  # Keep special chars for sentiment
        remove_stopwords=False        # Keep stopwords for sentiment
    )
    
    # Test samples (Indonesian YouTube comments)
    samples = [
        "😊 bgt!! keren banget kontennya @windah_abcd",
        "L ilham 😢😢😢 jelek bet",
        "omg mantap seklii!! 🔥🔥 gw suka",
        "jelek bet dah cape dah 😤😤",
        "bang windah pintar pilih game!!! ❤️💯",
        "https://youtube.com @user gila gila bnget 😂😂😂",
    ]
    
    print("=" * 60)
    print("NLP PREPROCESSOR - DEMO")
    print("=" * 60)
    
    for i, sample in enumerate(samples, 1):
        cleaned = prep.preprocess(sample)
        print(f"\n{i}. Original:")
        print(f"   {sample}")
        print(f"   Cleaned:")
        print(f"   {cleaned}")
    
    print("\n" + "=" * 60)
    print("Statistics:")
    print(prep.get_stats())
    print("=" * 60)
