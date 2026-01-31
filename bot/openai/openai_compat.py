"""
OpenAI compatibility layer for different versions.

This module provides a compatibility layer between OpenAI library versions:
- OpenAI < 1.0 (old API with openai.error module)
- OpenAI >= 1.0 (new API with direct exception imports)
"""

try:
    # Try new OpenAI >= 1.0 API
    from openai import (
        OpenAIError,
        RateLimitError,
        APIError,
        APIConnectionError,
        AuthenticationError,
        APITimeoutError,
        BadRequestError,
    )
    
    # Create a mock error module for backward compatibility
    class ErrorModule:
        OpenAIError = OpenAIError
        RateLimitError = RateLimitError
        APIError = APIError
        APIConnectionError = APIConnectionError
        AuthenticationError = AuthenticationError
        Timeout = APITimeoutError  # Renamed in new version
        InvalidRequestError = BadRequestError  # Renamed in new version
    
    error = ErrorModule()
    
    # Also export with new names
    Timeout = APITimeoutError
    InvalidRequestError = BadRequestError
    
except ImportError:
    # Fall back to old OpenAI < 1.0 API
    try:
        import openai.error as error
        
        # Export individual exceptions for direct import
        OpenAIError = error.OpenAIError
        RateLimitError = error.RateLimitError
        APIError = error.APIError
        APIConnectionError = error.APIConnectionError
        AuthenticationError = error.AuthenticationError
        InvalidRequestError = error.InvalidRequestError
        Timeout = error.Timeout
        BadRequestError = error.InvalidRequestError  # Alias
        APITimeoutError = error.Timeout  # Alias
    except (ImportError, AttributeError):
        # Neither version works, create dummy classes
        class OpenAIError(Exception):
            pass
        
        class RateLimitError(OpenAIError):
            pass
        
        class APIError(OpenAIError):
            pass
        
        class APIConnectionError(OpenAIError):
            pass
        
        class AuthenticationError(OpenAIError):
            pass
        
        class InvalidRequestError(OpenAIError):
            pass
        
        class Timeout(OpenAIError):
            pass
        
        BadRequestError = InvalidRequestError
        APITimeoutError = Timeout
        
        # Create error module
        class ErrorModule:
            OpenAIError = OpenAIError
            RateLimitError = RateLimitError
            APIError = APIError
            APIConnectionError = APIConnectionError
            AuthenticationError = AuthenticationError
            InvalidRequestError = InvalidRequestError
            Timeout = Timeout
        
        error = ErrorModule()

# Export all for easy import
__all__ = [
    'error',
    'OpenAIError',
    'RateLimitError',
    'APIError',
    'APIConnectionError',
    'AuthenticationError',
    'InvalidRequestError',
    'Timeout',
    'BadRequestError',
    'APITimeoutError',
]
