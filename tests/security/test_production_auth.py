"""
Comprehensive tests for production-grade JWT authentication system
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from src.common.security.auth import (
    ProductionTokenManager,
    TokenPair,
    KeyManager,
    RefreshTokenStore,
    create_token_pair,
    refresh_token_pair,
    verify_jwt_token,
    revoke_refresh_token
)

class TestKeyManager:
    """Test cryptographic key management"""
    
    def test_rsa_key_generation(self):
        """Test RSA key pair generation"""
        manager = KeyManager(algorithm="RS256")
        assert manager.private_key is not None
        assert manager.public_key is not None
        
        # Test PEM export
        private_pem = manager.get_private_key_pem()
        public_pem = manager.get_public_key_pem()
        
        assert "BEGIN PRIVATE KEY" in private_pem
        assert "BEGIN PUBLIC KEY" in public_pem
    
    def test_ecdsa_key_generation(self):
        """Test ECDSA key pair generation"""
        manager = KeyManager(algorithm="ES256")
        assert manager.private_key is not None
        assert manager.public_key is not None
    
    def test_unsupported_algorithm(self):
        """Test error handling for unsupported algorithms"""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            KeyManager(algorithm="HS256")

class TestRefreshTokenStore:
    """Test refresh token storage and management"""
    
    def test_store_and_validate_token(self):
        """Test token storage and validation"""
        store = RefreshTokenStore()
        jti = "test-jti-123"
        user_id = "user123"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        store.store_token(jti, user_id, expires_at)
        
        assert store.is_valid_token(jti) is True
        assert store.get_user_id(jti) == user_id
    
    def test_revoke_token(self):
        """Test token revocation"""
        store = RefreshTokenStore()
        jti = "test-jti-123"
        user_id = "user123"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        store.store_token(jti, user_id, expires_at)
        store.revoke_token(jti)
        
        assert store.is_valid_token(jti) is False
    
    def test_expired_token(self):
        """Test expired token validation"""
        store = RefreshTokenStore()
        jti = "test-jti-123"
        user_id = "user123"
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        
        store.store_token(jti, user_id, expires_at)
        
        assert store.is_valid_token(jti) is False
    
    def test_cleanup_expired(self):
        """Test cleanup of expired tokens"""
        store = RefreshTokenStore()
        
        # Add expired token
        expired_jti = "expired-jti"
        expired_expires = datetime.now(timezone.utc) - timedelta(hours=1)
        store.store_token(expired_jti, "user1", expired_expires)
        
        # Add valid token
        valid_jti = "valid-jti"
        valid_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        store.store_token(valid_jti, "user2", valid_expires)
        
        store.cleanup_expired()
        
        assert expired_jti not in store._tokens
        assert valid_jti in store._tokens

class TestProductionTokenManager:
    """Test production JWT token manager"""
    
    @pytest.fixture
    def token_manager(self):
        """Create token manager for testing"""
        return ProductionTokenManager(
            algorithm="RS256",
            access_token_ttl=900,  # 15 minutes
            refresh_token_ttl=3600  # 1 hour for testing
        )
    
    def test_generate_token_pair(self, token_manager):
        """Test token pair generation"""
        user_id = "test-user-123"
        scope = "read:pets write:pets"
        
        token_pair = token_manager.generate_token_pair(user_id, scope)
        
        assert isinstance(token_pair, TokenPair)
        assert token_pair.access_token
        assert token_pair.refresh_token
        assert token_pair.expires_in == 900
        assert token_pair.token_type == "Bearer"
    
    def test_verify_access_token(self, token_manager):
        """Test access token verification"""
        user_id = "test-user-123"
        scope = "read:pets"
        
        token_pair = token_manager.generate_token_pair(user_id, scope)
        payload = token_manager.verify_access_token(token_pair.access_token)
        
        assert payload is not None
        assert payload['sub'] == user_id
        assert payload['typ'] == 'access'
        assert payload['scope'] == scope
        assert payload['iss'] == token_manager.issuer
        assert payload['aud'] == token_manager.audience
    
    def test_verify_refresh_token(self, token_manager):
        """Test refresh token verification"""
        user_id = "test-user-123"
        
        token_pair = token_manager.generate_token_pair(user_id)
        payload = token_manager.verify_refresh_token(token_pair.refresh_token)
        
        assert payload is not None
        assert payload['sub'] == user_id
        assert payload['typ'] == 'refresh'
    
    def test_invalid_token_verification(self, token_manager):
        """Test verification of invalid tokens"""
        invalid_token = "invalid.token.here"
        
        assert token_manager.verify_access_token(invalid_token) is None
        assert token_manager.verify_refresh_token(invalid_token) is None
    
    def test_expired_token_verification(self, token_manager):
        """Test verification of expired tokens"""
        # Create token manager with very short TTL
        short_ttl_manager = ProductionTokenManager(
            algorithm="RS256",
            access_token_ttl=1,  # 1 second
            refresh_token_ttl=1
        )
        
        user_id = "test-user-123"
        token_pair = short_ttl_manager.generate_token_pair(user_id)
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        assert short_ttl_manager.verify_access_token(token_pair.access_token) is None
        assert short_ttl_manager.verify_refresh_token(token_pair.refresh_token) is None
    
    def test_refresh_tokens(self, token_manager):
        """Test token refresh functionality"""
        user_id = "test-user-123"
        scope = "read:pets"
        
        # Generate initial token pair
        initial_pair = token_manager.generate_token_pair(user_id, scope)
        
        # Refresh tokens
        new_pair = token_manager.refresh_tokens(initial_pair.refresh_token)
        
        assert new_pair is not None
        assert new_pair.access_token != initial_pair.access_token
        assert new_pair.refresh_token != initial_pair.refresh_token
        
        # Verify new tokens work
        payload = token_manager.verify_access_token(new_pair.access_token)
        assert payload['sub'] == user_id
        assert payload['scope'] == scope
        
        # Verify old refresh token is revoked
        assert token_manager.refresh_tokens(initial_pair.refresh_token) is None
    
    def test_revoke_refresh_token(self, token_manager):
        """Test refresh token revocation"""
        user_id = "test-user-123"
        
        token_pair = token_manager.generate_token_pair(user_id)
        
        # Revoke refresh token
        result = token_manager.revoke_refresh_token(token_pair.refresh_token)
        assert result is True
        
        # Try to use revoked token
        assert token_manager.refresh_tokens(token_pair.refresh_token) is None
    
    def test_wrong_token_type_verification(self, token_manager):
        """Test that access tokens can't be used as refresh tokens and vice versa"""
        user_id = "test-user-123"
        
        token_pair = token_manager.generate_token_pair(user_id)
        
        # Try to verify access token as refresh token
        assert token_manager.verify_refresh_token(token_pair.access_token) is None
        
        # Try to verify refresh token as access token
        assert token_manager.verify_access_token(token_pair.refresh_token) is None
    
    def test_get_jwks(self, token_manager):
        """Test JWKS generation"""
        jwks = token_manager.get_jwks()
        
        assert 'keys' in jwks
        assert len(jwks['keys']) > 0
        
        key = jwks['keys'][0]
        assert 'kty' in key
        assert 'use' in key
        assert 'alg' in key
        assert key['use'] == 'sig'
        assert key['alg'] == token_manager.algorithm

class TestGlobalFunctions:
    """Test global convenience functions"""
    
    def test_create_token_pair(self):
        """Test global create_token_pair function"""
        user_id = "test-user"
        scope = "read:pets"
        
        token_pair = create_token_pair(user_id, scope)
        
        assert isinstance(token_pair, TokenPair)
        assert token_pair.access_token
        assert token_pair.refresh_token
    
    def test_verify_jwt_token(self):
        """Test global verify_jwt_token function"""
        user_id = "test-user"
        
        token_pair = create_token_pair(user_id)
        payload = verify_jwt_token(token_pair.access_token)
        
        assert payload is not None
        assert payload['sub'] == user_id
    
    def test_refresh_token_pair_global(self):
        """Test global refresh_token_pair function"""
        user_id = "test-user"
        
        initial_pair = create_token_pair(user_id)
        new_pair = refresh_token_pair(initial_pair.refresh_token)
        
        assert new_pair is not None
        assert new_pair.access_token != initial_pair.access_token
    
    def test_revoke_refresh_token_global(self):
        """Test global revoke_refresh_token function"""
        user_id = "test-user"
        
        token_pair = create_token_pair(user_id)
        result = revoke_refresh_token(token_pair.refresh_token)
        
        assert result is True

class TestSecurityFeatures:
    """Test security-specific features"""
    
    def test_token_unique_jti(self):
        """Test that each token has a unique JTI"""
        user_id = "test-user"
        
        pair1 = create_token_pair(user_id)
        pair2 = create_token_pair(user_id)
        
        # Decode tokens to check JTI
        payload1 = jwt.decode(pair1.access_token, options={"verify_signature": False})
        payload2 = jwt.decode(pair2.access_token, options={"verify_signature": False})
        
        assert payload1['jti'] != payload2['jti']
    
    def test_token_contains_required_claims(self):
        """Test that tokens contain all required JWT claims"""
        user_id = "test-user"
        scope = "read:pets"
        
        token_pair = create_token_pair(user_id, scope)
        
        # Decode access token
        access_payload = jwt.decode(token_pair.access_token, options={"verify_signature": False})
        
        required_claims = ['sub', 'iat', 'exp', 'iss', 'aud', 'jti', 'typ']
        for claim in required_claims:
            assert claim in access_payload
        
        assert access_payload['sub'] == user_id
        assert access_payload['typ'] == 'access'
        assert access_payload['scope'] == scope
    
    def test_token_algorithm_in_header(self):
        """Test that token header contains correct algorithm"""
        user_id = "test-user"
        
        token_pair = create_token_pair(user_id)
        
        # Decode header
        header = jwt.get_unverified_header(token_pair.access_token)
        
        assert header['alg'] == 'RS256'
        assert header['typ'] == 'JWT'

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_malformed_token(self):
        """Test handling of malformed tokens"""
        malformed_tokens = [
            "not.a.token",
            "too.few.parts",
            "too.many.parts.here.extra",
            "",
            None
        ]
        
        for token in malformed_tokens:
            if token is not None:
                assert verify_jwt_token(token) is None
    
    def test_refresh_with_access_token(self):
        """Test refresh attempt with access token instead of refresh token"""
        user_id = "test-user"
        
        token_pair = create_token_pair(user_id)
        
        # Try to refresh with access token
        result = refresh_token_pair(token_pair.access_token)
        assert result is None
    
    def test_revoke_invalid_token(self):
        """Test revoking invalid tokens"""
        result = revoke_refresh_token("invalid.token.here")
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__])