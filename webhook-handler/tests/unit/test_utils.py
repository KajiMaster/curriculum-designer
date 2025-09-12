"""Tests for utility modules."""

import pytest
from unittest.mock import Mock, patch
import boto3
from botocore.exceptions import ClientError

from src.utils import SecretsManager, get_secrets_manager, get_trello_api_key, ErrorBoundary


class TestSecretsManager:
    """Test secrets manager."""
    
    def test_get_secret_from_cache(self):
        """Test getting secret from cache."""
        manager = SecretsManager()
        manager._cache["TEST_PARAM:TEST_ENV"] = "cached_value"
        
        result = manager.get_secret("TEST_PARAM", "TEST_ENV")
        assert result == "cached_value"
    
    def test_get_secret_from_env(self):
        """Test getting secret from environment variable."""
        manager = SecretsManager()
        
        with patch.dict('os.environ', {'TEST_ENV': 'env_value'}):
            with patch('src.config.Config.is_lambda_environment', return_value=False):
                result = manager.get_secret("TEST_PARAM", "TEST_ENV")
                assert result == "env_value"
    
    @patch('src.config.Config.is_lambda_environment', return_value=True)
    def test_get_secret_from_ssm(self, mock_lambda_env):
        """Test getting secret from SSM Parameter Store."""
        manager = SecretsManager()
        
        mock_ssm = Mock()
        mock_ssm.get_parameter.return_value = {
            'Parameter': {'Value': 'ssm_value'}
        }
        manager._ssm_client = mock_ssm
        
        with patch('src.config.Config.TRELLO_API_KEY_PARAM', '/test/param'):
            result = manager.get_secret("TRELLO_API_KEY_PARAM", "FALLBACK")
            assert result == "ssm_value"
            mock_ssm.get_parameter.assert_called_once_with(
                Name='/test/param',
                WithDecryption=True
            )
    
    @patch('src.config.Config.is_lambda_environment', return_value=True)
    def test_get_secret_ssm_error_fallback(self, mock_lambda_env):
        """Test fallback to env var when SSM fails."""
        manager = SecretsManager()
        
        mock_ssm = Mock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {'Error': {'Code': 'ParameterNotFound'}},
            'GetParameter'
        )
        manager._ssm_client = mock_ssm
        
        with patch.dict('os.environ', {'FALLBACK': 'fallback_value'}):
            with patch('src.config.Config.TRELLO_API_KEY_PARAM', '/test/param'):
                result = manager.get_secret("TRELLO_API_KEY_PARAM", "FALLBACK")
                assert result == "fallback_value"
    
    def test_clear_cache(self):
        """Test clearing secrets cache."""
        manager = SecretsManager()
        manager._cache["TEST"] = "value"
        
        manager.clear_cache()
        assert len(manager._cache) == 0
    
    def test_get_secrets_manager_singleton(self):
        """Test that get_secrets_manager returns singleton."""
        manager1 = get_secrets_manager()
        manager2 = get_secrets_manager()
        
        assert manager1 is manager2


class TestErrorBoundary:
    """Test error boundary context manager."""
    
    def test_error_boundary_no_exception(self):
        """Test error boundary with no exceptions."""
        with ErrorBoundary("test_context") as boundary:
            result = 1 + 1
        
        assert result == 2
    
    def test_error_boundary_with_exception(self):
        """Test error boundary catches and logs exception."""
        mock_logger = Mock()
        
        with pytest.raises(ValueError):
            with ErrorBoundary("test_context", logger=mock_logger):
                raise ValueError("Test error")
        
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Error in test_context" in error_msg
    
    def test_error_boundary_default_logger(self):
        """Test error boundary with default logger."""
        with pytest.raises(RuntimeError):
            with ErrorBoundary("test_operation"):
                raise RuntimeError("Test runtime error")


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('src.utils.get_secrets_manager')
    def test_get_trello_api_key(self, mock_get_manager):
        """Test get_trello_api_key convenience function."""
        mock_manager = Mock()
        mock_manager.get_secret.return_value = "test_api_key"
        mock_get_manager.return_value = mock_manager
        
        result = get_trello_api_key()
        
        assert result == "test_api_key"
        mock_manager.get_secret.assert_called_once_with(
            "TRELLO_API_KEY_PARAM",
            "TRELLO_API_KEY"
        )