import pytest
from src.bot.i18n import simple_gettext


class TestFinalLocalizationFixes:
    """Tests for the final localization fixes"""
    
    def test_rate_limiter_translations(self):
        """Test rate limiter translations"""
        # Test Russian
        assert simple_gettext('ru', 'commands') == 'команд'
        assert simple_gettext('ru', 'messages') == 'сообщений'
        assert 'Превышен лимит' in simple_gettext('ru', 'Rate limit exceeded for {limit_type} per minute.\nPlease wait a moment before the next request.')
        
        # Test Uzbek
        assert simple_gettext('uz', 'commands') == 'buyruqlar'
        assert simple_gettext('uz', 'messages') == 'xabarlar'
        assert 'limiti oshib ketdi' in simple_gettext('uz', 'Rate limit exceeded for {limit_type} per minute.\nPlease wait a moment before the next request.')
    
    def test_field_protection_translations(self):
        """Test field protection explanation translations"""
        # Test Russian
        ru_text = simple_gettext('ru', "This field is protected because it's already filled and affects your credit score. This ensures the reliability of your assessment.")
        assert 'защищено' in ru_text
        assert 'кредитный рейтинг' in ru_text
        
        # Test Uzbek
        uz_text = simple_gettext('uz', "This field is protected because it's already filled and affects your credit score. This ensures the reliability of your assessment.")
        assert 'himoyalangan' in uz_text
        assert 'kredit reyting' in uz_text
    
    def test_pdn_description_translations(self):
        """Test PDN description translations"""
        # Test Russian
        assert simple_gettext('ru', 'DTI') == 'ПДН'
        assert 'Отличный показатель' in simple_gettext('ru', 'Excellent indicator! Banks will readily approve the loan.')
        assert 'Приемлемый показатель' in simple_gettext('ru', 'Acceptable indicator. Loan approval is possible.')
        assert 'Высокая долговая нагрузка' in simple_gettext('ru', "High debt burden! Banks won't be able to issue a loan.")
        
        # Test Uzbek
        assert simple_gettext('uz', 'DTI') == 'PDN'
        assert "A'lo ko'rsatkich" in simple_gettext('uz', 'Excellent indicator! Banks will readily approve the loan.')
        assert 'Qoniqarli ko'rsatkich' in simple_gettext('uz', 'Acceptable indicator. Loan approval is possible.')
        assert 'Yuqori qarz yuki' in simple_gettext('uz', "High debt burden! Banks won't be able to issue a loan.")
    
    def test_all_core_error_messages_translated(self):
        """Test that all core error messages have translations"""
        error_messages = [
            'Invalid calculation parameters',
            'Income must be positive',
            'Loan amount must be positive',
            'Amount exceeds maximum for {loan_type}: {max_amount} sum',
            'Rate must be between {min_rate}% and {max_rate}%',
            'Term must be from {min_term} to {max_term} months',
            'Cannot use your own referral link'
        ]
        
        for msg in error_messages:
            # Russian translation should be different from English
            ru_trans = simple_gettext('ru', msg)
            assert ru_trans != msg, f"Missing Russian translation for: {msg}"
            
            # Uzbek translation should be different from English
            uz_trans = simple_gettext('uz', msg)
            assert uz_trans != msg, f"Missing Uzbek translation for: {msg}"
    
    def test_all_scoring_criteria_translated(self):
        """Test that all scoring criteria have translations"""
        criteria = [
            'Age ≥ 35 years',
            'Female gender',
            'Work experience ≥ 24 months',
            'Living at address ≥ 3 years',
            'Own home without mortgage',
            'Married',
            'Higher education',
            'Closed loans ≥ 3',
            'Has other loans but DTI ≤ 50%',
            'Tashkent or Tashkent region',
            'Apple device',
            'Referrals ({count} people)'
        ]
        
        for criterion in criteria:
            # Russian translation should be different from English
            ru_trans = simple_gettext('ru', criterion)
            assert ru_trans != criterion, f"Missing Russian translation for: {criterion}"
            
            # Uzbek translation should be different from English
            uz_trans = simple_gettext('uz', criterion)
            assert uz_trans != criterion, f"Missing Uzbek translation for: {criterion}"
    
    def test_all_field_names_translated(self):
        """Test that all field names have translations"""
        field_names = [
            'Age',
            'Gender',
            'Work experience',
            'Address stability',
            'Housing status',
            'Marital status',
            'Education',
            'Number of closed loans',
            'Region of residence',
            'Monthly income',
            'Other loans available',
            'Other loan payments'
        ]
        
        for field in field_names:
            # Russian translation should be different from English
            ru_trans = simple_gettext('ru', field)
            assert ru_trans != field, f"Missing Russian translation for: {field}"
            
            # Uzbek translation should be different from English
            uz_trans = simple_gettext('uz', field)
            assert uz_trans != field, f"Missing Uzbek translation for: {field}"
    
    def test_score_levels_translated(self):
        """Test that all score levels have translations"""
        levels = [
            'Excellent',
            'Good', 
            'Average',
            'Below average',
            'Low'
        ]
        
        for level in levels:
            # Russian translation should be different from English
            ru_trans = simple_gettext('ru', level)
            assert ru_trans != level, f"Missing Russian translation for: {level}"
            
            # Uzbek translation should be different from English
            uz_trans = simple_gettext('uz', level)
            assert uz_trans != level, f"Missing Uzbek translation for: {level}"
    
    def test_score_message_formatting_translated(self):
        """Test score message formatting strings"""
        messages = [
            'Your credit score: {score}',
            'Level: {level}',
            'Breakdown:'
        ]
        
        for msg in messages:
            # Russian translation should be different from English
            ru_trans = simple_gettext('ru', msg)
            assert ru_trans != msg, f"Missing Russian translation for: {msg}"
            
            # Uzbek translation should be different from English  
            uz_trans = simple_gettext('uz', msg)
            assert uz_trans != msg, f"Missing Uzbek translation for: {msg}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])