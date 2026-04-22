"""
Prompt loader module for loading and managing prompts
"""
import os
from typing import Dict, Any, Optional
from loguru import logger


class PromptLoader:
    """Class to load and manage prompts"""
    
    def __init__(self, prompt_dir: str = "prompts"):
        self.prompt_dir = prompt_dir
        self._prompts: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompts from the prompt directory"""
        if os.path.exists(self.prompt_dir):
            for filename in os.listdir(self.prompt_dir):
                if filename.endswith('.txt'):
                    prompt_name = filename[:-4]  # Remove .txt extension
                    filepath = os.path.join(self.prompt_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            self._prompts[prompt_name] = f.read().strip()
                    except Exception as e:
                        logger.error(f"Error loading prompt {filename}: {e}")
        else:
            logger.warning(f"Prompt directory {self.prompt_dir} does not exist")
    
    def load_prompt(self, name: str) -> Optional[str]:
        """Load a specific prompt by name"""
        return self._prompts.get(name)
    
    def load_util(self, name: str) -> str:
        """Load a utility prompt by name"""
        return self._prompts.get(name, "")
    
    def add_prompt(self, name: str, content: str):
        """Add a prompt to the loader"""
        self._prompts[name] = content
    
    def reload(self):
        """Reload all prompts"""
        self._prompts.clear()
        self._load_prompts()


# Global instance
prompt_loader = PromptLoader()
