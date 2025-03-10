import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ContentReviewer:
    """
    A utility class for reviewing and identifying issues in generated content.
    Used as a final check before content is delivered to users.
    """
    
    # Patterns to identify common issues
    PATTERNS = {
        "name_placeholder": r"\[\s*[Ии]мя\s*автора\s*\]",
        "single_word_sentence": r"(?<=[.?!]\s)[А-ЯЁA-Z][а-яёa-z]{1,5}[.?!](\s|$)",
        "awkward_phrases": [
            "создател[яю] учебных курсов",
            "иллюзии всемогущества",
            "глухого угла в собственном деле"
        ],
        "incorrect_terminology": {
            "бизнес": "дело",
            "предпринимательств[оа]": "своё дело"
        },
        "short_paragraphs": r"(?m)^[^.\n]{1,50}[.?!]$"
    }
    
    def __init__(self, author_name="Сергей Черненко"):
        """
        Initialize the content reviewer.
        
        Args:
            author_name (str): The correct author name to check for
        """
        self.author_name = author_name
    
    def _ensure_string(self, content):
        """
        Ensure the content is a string.
        
        Args:
            content: The content to convert to string
            
        Returns:
            str: String representation of the content
        """
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        
        try:
            return str(content)
        except Exception as e:
            logger.error(f"Failed to convert content to string: {str(e)}")
            return ""
    
    def review_content(self, content):
        """
        Review the content for common issues.
        
        Args:
            content: The content to review (string or object with string representation)
            
        Returns:
            dict: A dictionary of issues found in the content
        """
        # Ensure content is a string
        content_str = self._ensure_string(content)
        
        issues = {
            "name_placeholders": [],
            "author_missing": False,
            "single_word_sentences": [],
            "awkward_phrases": [],
            "terminology_issues": [],
            "short_paragraphs": [],
            "statistics_issues": []
        }
        
        try:
            # Check for name placeholders
            name_placeholders = re.findall(self.PATTERNS["name_placeholder"], content_str)
            if name_placeholders:
                issues["name_placeholders"] = name_placeholders
                
            # Check if author name is correctly used
            if self.author_name not in content_str:
                issues["author_missing"] = True
                
            # Check for single word sentences
            single_word_sentences = re.findall(self.PATTERNS["single_word_sentence"], content_str)
            if single_word_sentences:
                issues["single_word_sentences"] = single_word_sentences
                
            # Check for awkward phrases
            for phrase in self.PATTERNS["awkward_phrases"]:
                matches = re.findall(phrase, content_str, re.IGNORECASE)
                if matches:
                    issues["awkward_phrases"].extend(matches)
                    
            # Check for incorrect terminology
            for incorrect, correct in self.PATTERNS["incorrect_terminology"].items():
                matches = re.findall(incorrect, content_str, re.IGNORECASE)
                if matches:
                    issues["terminology_issues"].append(f"Используется '{incorrect}' вместо '{correct}'")
                    
            # Check for short paragraphs
            short_paragraphs = re.findall(self.PATTERNS["short_paragraphs"], content_str)
            if short_paragraphs:
                issues["short_paragraphs"] = short_paragraphs
                
            # Check for statistics issues (harder to detect automatically, basic check)
            if re.search(r'\d+%|\d+\s*рублей|\d+\s*тысяч', content_str):
                # Look for statistical assertions without context
                if re.search(r'(?<![А-Яа-я])\d+%(?![А-Яа-я])', content_str):
                    issues["statistics_issues"].append("Цифры без контекста")
        
        except Exception as e:
            logger.error(f"Error in review_content: {str(e)}")
            # Add an error message to the issues
            issues["error"] = str(e)
        
        return issues
    
    def get_review_summary(self, content):
        """
        Get a summary of issues found in the content.
        
        Args:
            content: The content to review (string or object with string representation)
            
        Returns:
            str: A summary of issues found
        """
        try:
            issues = self.review_content(content)
            
            # If there was an error during review, return a simplified summary
            if "error" in issues:
                return f"❌ Ошибка при проверке контента: {issues['error']}"
            
            # Count total issues
            total_issues = sum(
                len(value) if isinstance(value, list) else (1 if value else 0)
                for key, value in issues.items() if key != "error"
            )
            
            summary = f"Всего найдено проблем: {total_issues}\n\n"
            
            if issues["name_placeholders"]:
                summary += f"❌ Найдены плейсхолдеры имени: {len(issues['name_placeholders'])}\n"
            else:
                summary += "✅ Плейсхолдеры имени не найдены\n"
                
            if issues["author_missing"]:
                summary += f"❌ Имя автора ({self.author_name}) отсутствует\n"
            else:
                summary += f"✅ Имя автора ({self.author_name}) присутствует\n"
                
            if issues["single_word_sentences"]:
                summary += f"❌ Найдены одиночные слова как предложения: {len(issues['single_word_sentences'])}\n"
            else:
                summary += "✅ Нет одиночных слов в качестве предложений\n"
                
            if issues["awkward_phrases"]:
                summary += f"❌ Найдены неуклюжие фразы: {len(issues['awkward_phrases'])}\n"
            else:
                summary += "✅ Неуклюжие фразы не найдены\n"
                
            if issues["terminology_issues"]:
                summary += f"❌ Проблемы с терминологией: {len(issues['terminology_issues'])}\n"
            else:
                summary += "✅ Проблем с терминологией не обнаружено\n"
                
            if issues["short_paragraphs"]:
                summary += f"❌ Короткие абзацы: {len(issues['short_paragraphs'])}\n"
            else:
                summary += "✅ Коротких абзацев не обнаружено\n"
                
            if issues["statistics_issues"]:
                summary += f"❌ Проблемы со статистикой: {len(issues['statistics_issues'])}\n"
            else:
                summary += "✅ Проблем со статистикой не обнаружено\n"
                
            return summary
            
        except Exception as e:
            logger.error(f"Error in get_review_summary: {str(e)}")
            return f"❌ Ошибка при создании отчета: {str(e)}"
    
    def get_detailed_report(self, content):
        """
        Get a detailed report of issues found in the content.
        
        Args:
            content: The content to review (string or object with string representation)
            
        Returns:
            str: A detailed report of issues found
        """
        try:
            # Ensure content is a string
            content_str = self._ensure_string(content)
            
            issues = self.review_content(content_str)
            
            # If there was an error during review, return a simplified report
            if "error" in issues:
                return f"❌ Ошибка при проверке контента: {issues['error']}"
                
            summary = self.get_review_summary(content_str)
            
            report = f"{summary}\n\nДЕТАЛИ ПРОБЛЕМ:\n\n"
            
            if issues["name_placeholders"]:
                report += "ПЛЕЙСХОЛДЕРЫ ИМЕНИ:\n"
                for placeholder in issues["name_placeholders"]:
                    report += f"- {placeholder}\n"
                report += "\n"
                
            if issues["single_word_sentences"]:
                report += "ОДИНОЧНЫЕ СЛОВА КАК ПРЕДЛОЖЕНИЯ:\n"
                for sentence in issues["single_word_sentences"]:
                    report += f"- {sentence.strip()}\n"
                report += "\n"
                
            if issues["awkward_phrases"]:
                report += "НЕУКЛЮЖИЕ ФРАЗЫ:\n"
                for phrase in issues["awkward_phrases"]:
                    report += f"- {phrase}\n"
                report += "\n"
                
            if issues["terminology_issues"]:
                report += "ПРОБЛЕМЫ С ТЕРМИНОЛОГИЕЙ:\n"
                for issue in issues["terminology_issues"]:
                    report += f"- {issue}\n"
                report += "\n"
                
            if issues["short_paragraphs"]:
                report += "КОРОТКИЕ АБЗАЦЫ:\n"
                for paragraph in issues["short_paragraphs"][:5]:  # Limit to 5 examples
                    report += f"- {paragraph.strip()}\n"
                if len(issues["short_paragraphs"]) > 5:
                    report += f"  и еще {len(issues['short_paragraphs']) - 5}...\n"
                report += "\n"
                
            if issues["statistics_issues"]:
                report += "ПРОБЛЕМЫ СО СТАТИСТИКОЙ:\n"
                for issue in issues["statistics_issues"]:
                    report += f"- {issue}\n"
                report += "\n"
                
            return report
            
        except Exception as e:
            logger.error(f"Error in get_detailed_report: {str(e)}")
            return f"❌ Ошибка при создании детального отчета: {str(e)}"
    
    def fix_common_issues(self, content):
        """
        Fix common issues in the content automatically.
        
        Args:
            content: The content to fix (string or object with string representation)
            
        Returns:
            str: The fixed content
        """
        try:
            # Ensure content is a string
            content_str = self._ensure_string(content)
            
            # Replace name placeholders with author name
            fixed_content = re.sub(
                self.PATTERNS["name_placeholder"], 
                self.author_name, 
                content_str
            )
            
            # Fix incorrect terminology
            for incorrect, correct in self.PATTERNS["incorrect_terminology"].items():
                fixed_content = re.sub(
                    incorrect, 
                    correct, 
                    fixed_content, 
                    flags=re.IGNORECASE
                )
            
            return fixed_content
            
        except Exception as e:
            logger.error(f"Error in fix_common_issues: {str(e)}")
            # If we can't fix the content, return it unchanged
            return self._ensure_string(content) 