import pytest
import os
import ast
from pathlib import Path
from src.bot.i18n import simple_gettext, TRANSLATIONS


class TestI18nCompleteness:
    """Tests for translation completeness"""
    
    def test_all_russian_keys_have_uzbek_translations(self):
        """All Russian keys should have Uzbek translations"""
        ru_keys = set(TRANSLATIONS['ru'].keys())
        uz_keys = set(TRANSLATIONS['uz'].keys())
        
        missing_keys = ru_keys - uz_keys
        assert not missing_keys, f"Missing Uzbek translations for: {missing_keys}"
    
    def test_all_uzbek_keys_have_russian_translations(self):
        """All Uzbek keys should have Russian translations"""
        ru_keys = set(TRANSLATIONS['ru'].keys())
        uz_keys = set(TRANSLATIONS['uz'].keys())
        
        missing_keys = uz_keys - ru_keys
        assert not missing_keys, f"Missing Russian translations for: {missing_keys}"
    
    def test_no_empty_translations(self):
        """Translations should not be empty"""
        for lang in ['ru', 'uz']:
            for key, value in TRANSLATIONS[lang].items():
                assert value.strip(), f"Empty translation for '{key}' in {lang}"
    
    def test_format_strings_consistency(self):
        """Check format string placeholders are consistent across languages"""
        import re
        
        # Get common keys
        common_keys = set(TRANSLATIONS['ru'].keys()) & set(TRANSLATIONS['uz'].keys())
        
        for key in common_keys:
            ru_value = TRANSLATIONS['ru'][key]
            uz_value = TRANSLATIONS['uz'][key]
            
            # Find all format placeholders
            ru_placeholders = set(re.findall(r'\{[^}]+\}', ru_value))
            uz_placeholders = set(re.findall(r'\{[^}]+\}', uz_value))
            
            assert ru_placeholders == uz_placeholders, \
                f"Placeholder mismatch for '{key}': RU={ru_placeholders}, UZ={uz_placeholders}"
    
    def test_po_files_exist(self):
        """Check that .po files exist"""
        po_dir = Path(__file__).parent.parent.parent / 'src' / 'bot' / 'i18n'
        
        assert (po_dir / 'ru.po').exists(), "Russian .po file not found"
        assert (po_dir / 'uz.po').exists(), "Uzbek .po file not found"
    
    def test_po_files_valid(self):
        """Check that .po files are valid"""
        try:
            import polib
        except ImportError:
            pytest.skip("polib not installed")
        
        po_dir = Path(__file__).parent.parent.parent / 'src' / 'bot' / 'i18n'
        
        # Test Russian .po file
        ru_po = polib.pofile(str(po_dir / 'ru.po'))
        assert len(ru_po) > 0, "Russian .po file is empty"
        
        # Test Uzbek .po file
        uz_po = polib.pofile(str(po_dir / 'uz.po'))
        assert len(uz_po) > 0, "Uzbek .po file is empty"
        
        # Check that both files have the same number of entries
        assert len(ru_po) == len(uz_po), \
            f"Different number of entries: RU={len(ru_po)}, UZ={len(uz_po)}"


class TestHardcodedStringsRemoved:
    """Test that hardcoded strings have been removed from the codebase"""
    
    def get_python_files(self, directory):
        """Get all Python files in a directory"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip test directories
            if 'test' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def check_file_for_hardcoded_strings(self, filepath, hardcoded_strings):
        """Check a file for hardcoded strings"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found_strings = []
        for hardcoded in hardcoded_strings:
            if hardcoded in content:
                # Check if it's in a comment or docstring
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if hardcoded in line:
                        # Simple check - not in a comment
                        stripped = line.strip()
                        if not stripped.startswith('#') and not stripped.startswith('"""'):
                            found_strings.append((hardcoded, i+1))
        
        return found_strings
    
    def test_no_hardcoded_russian_in_handlers(self):
        """Test that handler files don't contain hardcoded Russian strings"""
        hardcoded_strings = [
            "Справка по использованию бота",
            "Сколько лет вы проживаете",
            "Укажите ваш статус жилья:",
            "Укажите ваше семейное положение:",
            "Укажите ваш уровень образования:",
            "В каком регионе вы проживаете?",
            "Данные успешно сохранены!",
            "Количество кредитов"
        ]
        
        handlers_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', 'src', 'bot', 'handlers'
        )
        
        python_files = self.get_python_files(handlers_dir)
        
        all_found = []
        for filepath in python_files:
            found = self.check_file_for_hardcoded_strings(filepath, hardcoded_strings)
            if found:
                all_found.extend([(filepath, s, line) for s, line in found])
        
        assert not all_found, f"Found hardcoded strings: {all_found}"
    
    def test_no_hardcoded_regions_in_keyboards(self):
        """Test that keyboards.py doesn't contain hardcoded region names"""
        hardcoded_regions = [
            '"Андижан"', '"Бухара"', '"Фергана"', '"Джизак"',
            '"Наманган"', '"Навои"', '"Кашкадарья"', '"Самарканд"',
            '"Сырдарья"', '"Сурхандарья"', '"Хорезм"', '"Каракалпакстан"'
        ]
        
        keyboards_file = os.path.join(
            os.path.dirname(__file__), '..', '..', 'src', 'bot', 'keyboards.py'
        )
        
        found = self.check_file_for_hardcoded_strings(keyboards_file, hardcoded_regions)
        assert not found, f"Found hardcoded region names: {found}"
    
    def test_no_hardcoded_errors_in_core(self):
        """Test that core modules don't contain hardcoded error messages"""
        hardcoded_errors = [
            '"Некорректные параметры для расчета"',
            '"Доход должен быть положительным"',
            '"Сумма кредита должна быть положительной"',
            '"Нельзя использовать собственную реферальную ссылку"'
        ]
        
        core_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', 'src', 'core'
        )
        
        python_files = self.get_python_files(core_dir)
        
        all_found = []
        for filepath in python_files:
            found = self.check_file_for_hardcoded_strings(filepath, hardcoded_errors)
            if found:
                all_found.extend([(filepath, s, line) for s, line in found])
        
        assert not all_found, f"Found hardcoded error messages: {all_found}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])