"""
LangChain Tools for Virtual Human Assistant
Provides tool definitions and management using LangChain's tool system
"""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from backend.utils.logger import get_logger


# Initialize logger for this module
logger = get_logger(__name__)


@tool
async def get_weather(location: str) -> str:
    """
    Get the current weather for a location
    
    Args:
        location (str): The location to get weather for
        
    Returns:
        str: Weather information for the location
    """
    logger.info(f"Getting weather for: {location}")
    # This is a placeholder implementation
    # In a real application, this would call a weather API
    return f"The weather in {location} is sunny and 25°C"


@tool
async def get_time(timezone: str = "UTC") -> str:
    """
    Get the current time in a specific timezone
    
    Args:
        timezone (str): The timezone to get time for (default: UTC)
        
    Returns:
        str: Current time in the specified timezone
    """
    logger.info(f"Getting time for timezone: {timezone}")
    # This is a placeholder implementation
    # In a real application, this would use a time API or library
    from datetime import datetime
    return f"Current time in {timezone}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


@tool
async def calculate(expression: str) -> str:
    """
    Calculate the result of a mathematical expression
    
    Args:
        expression (str): The mathematical expression to calculate
        
    Returns:
        str: Result of the calculation
    """
    logger.info(f"Calculating expression: {expression}")
    # This is a placeholder implementation
    # In a real application, this would use a safe calculation library
    try:
        # Simple calculation for demonstration
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating expression: {str(e)}"


class ToolManager:
    """Tool manager for LangChain tools"""
    
    def __init__(self):
        """Initialize the tool manager"""
        self.tools = [get_weather, get_time, calculate]
        logger.info(f"ToolManager initialized with {len(self.tools)} tools")
    
    def get_tools(self) -> List[Any]:
        """
        Get all available tools
        
        Returns:
            List[Any]: List of available tools
        """
        return self.tools
    
    def get_tool_by_name(self, name: str) -> Optional[Any]:
        """
        Get a tool by name
        
        Args:
            name (str): Name of the tool
            
        Returns:
            Optional[Any]: Tool with the given name, or None if not found
        """
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
    def add_tool(self, tool_func):
        """
        Add a new tool
        
        Args:
            tool_func: Tool function to add
        """
        self.tools.append(tool_func)
        logger.info(f"Added tool: {tool_func.__name__}")
    
    def remove_tool(self, name: str):
        """
        Remove a tool by name
        
        Args:
            name (str): Name of the tool to remove
        """
        self.tools = [tool for tool in self.tools if tool.__name__ != name]
        logger.info(f"Removed tool: {name}")


# Global tool manager instance
tool_manager = None


def get_tool_manager() -> ToolManager:
    """
    Get or create the tool manager instance
    
    Returns:
        ToolManager: Tool manager instance
    """
    global tool_manager
    if tool_manager is None:
        tool_manager = ToolManager()
    return tool_manager
