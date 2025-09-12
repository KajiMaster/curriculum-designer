"""Tests for configuration module."""

import pytest
from unittest.mock import patch
import os

from src.config import Config, get_config


class TestConfig:
    """Test configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.LOG_LEVEL == "INFO"
        assert config.AWS_REGION == "us-east-1"
        assert config.FRAMEWORKS_TABLE == "curriculum-frameworks"
        assert config.FEEDBACK_TABLE == "lesson-plan-feedback"
        assert config.MAX_RETRIES == 3
        assert config.TIMEOUT_SECONDS == 30
    
    def test_is_lambda_environment(self):
        """Test Lambda environment detection."""
        config = Config()
        
        # Not in Lambda by default
        assert config.is_lambda_environment() is False
        
        # Simulate Lambda environment
        with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'test-function'}):
            assert config.is_lambda_environment() is True
    
    def test_validate_in_lambda(self):
        """Test configuration validation in Lambda environment."""
        with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'test-function'}):
            config = Config()
            
            # Should raise if required params are missing
            with pytest.raises(ValueError) as exc_info:
                config.validate()
            
            assert "Missing required configuration" in str(exc_info.value)
    
    def test_get_config_singleton(self):
        """Test that get_config returns singleton instance."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_environment_variable_override(self):
        """Test environment variable overrides."""
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'DEBUG',
            'AWS_REGION': 'us-west-2',
            'MAX_RETRIES': '5'
        }):
            # Clear the cache to force reload
            get_config.cache_clear()
            config = get_config()
            
            assert config.LOG_LEVEL == 'DEBUG'
            assert config.AWS_REGION == 'us-west-2'
            assert config.MAX_RETRIES == 5
            
            # Clear cache again for other tests
            get_config.cache_clear()
    
    def test_parameter_store_names(self):
        """Test parameter store configuration."""
        # Test with environment variables set
        with patch.dict(os.environ, {
            'TRELLO_API_KEY_PARAM': '/curriculum-designer/trello/api-key',
            'TRELLO_TOKEN_PARAM': '/curriculum-designer/trello/token',
            'OPENAI_API_KEY_PARAM': '/curriculum-designer/openai/api-key',
            'TRELLO_WEBHOOK_SECRET_PARAM': '/curriculum-designer/trello/webhook-secret'
        }):
            get_config.cache_clear()
            config = get_config()
            
            assert config.TRELLO_API_KEY_PARAM == "/curriculum-designer/trello/api-key"
            assert config.TRELLO_TOKEN_PARAM == "/curriculum-designer/trello/token"
            assert config.OPENAI_API_KEY_PARAM == "/curriculum-designer/openai/api-key"
            assert config.TRELLO_WEBHOOK_SECRET_PARAM == "/curriculum-designer/trello/webhook-secret"
            
            get_config.cache_clear()
    
    def test_lambda_function_names(self):
        """Test Lambda function names."""
        config = Config()
        
        assert config.ACTIVITY_GENERATOR_FUNCTION == "curriculum-activity-generator"
        assert config.MCP_SERVICE_FUNCTION == "curriculum-mcp-service"