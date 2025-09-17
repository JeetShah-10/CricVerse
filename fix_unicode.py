#!/usr/bin/env python3
"""
Fix Unicode emoji characters in test files for Windows compatibility
"""

import os
import re

def fix_unicode_in_file(filepath):
    """Fix Unicode emoji characters in a file"""
    if not os.path.exists(filepath):
        return False
    
    # Skip CSS, JS, and HTML files to avoid breaking styling
    if filepath.endswith(('.css', '.js', '.html', '.htm')):
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace common emoji characters with text equivalents
    replacements = {
        '🔐': '[SECURITY]',
        '✅': '[PASS]',
        '❌': '[FAIL]',
        '⚠️': '[WARN]',
        '🚀': '[START]',
        '📱': '[QR]',
        '🤖': '[BOT]',
        '⚡': '[PERF]',
        '🔧': '[FIX]',
        '📊': '[STATS]',
        '🎉': '[SUCCESS]',
        '🏆': '[TROPHY]',
        '📝': '[NOTE]',
        '💡': '[TIP]',
        '🟢': '[GOOD]',
        '🟡': '[OK]',
        '🟠': '[SLOW]',
        '🔴': '[BAD]',
        '📈': '[UP]',
        '📋': '[REPORT]',
        '🌏': '[WORLD]',
        '🏏': '[CRICKET]',
        '⏰': '[TIME]',
        '🔍': '[SEARCH]',
        '📞': '[PHONE]',
        '🌐': '[WEB]',
        '💻': '[COMPUTER]',
        '🔒': '[LOCK]',
        '🔓': '[UNLOCK]',
        '📧': '[EMAIL]',
        '📄': '[DOC]',
        '📁': '[FOLDER]',
        '📂': '[FOLDER_OPEN]',
        '🔗': '[LINK]',
        '📌': '[PIN]',
        '📍': '[LOCATION]',
        '🎯': '[TARGET]',
        '⚙️': '[SETTINGS]',
        '🛠️': '[TOOLS]',
        '🔨': '[HAMMER]',
        '⚒️': '[PICKAXE]',
        '🔩': '[NUT]',
        '⚡': '[LIGHTNING]',
        '🔥': '[FIRE]',
        '💧': '[WATER]',
        '🌊': '[WAVE]',
        '🌪️': '[TORNADO]',
        '🌈': '[RAINBOW]',
        '☀️': '[SUN]',
        '🌙': '[MOON]',
        '⭐': '[STAR]',
        '🌟': '[STAR_BRIGHT]',
        '💫': '[DIZZY]',
        '✨': '[SPARKLES]',
        '🎊': '[CONFETTI]',
        '🎈': '[BALLOON]',
        '🎁': '[GIFT]',
        '🎀': '[RIBBON]',
        '🏅': '[MEDAL]',
        '🥇': '[GOLD]',
        '🥈': '[SILVER]',
        '🥉': '[BRONZE]',
        '🏆': '[TROPHY]',
        '🎖️': '[MILITARY]',
        '🏵️': '[ROSETTE]',
        '🎗️': '[REMINDER]',
        '🎫': '[TICKET]',
        '🎟️': '[ADMISSION]',
        '🎪': '[CIRCUS]',
        '🎭': '[PERFORMING]',
        '🎨': '[ART]',
        '🎬': '[CLAPPER]',
        '🎤': '[MIC]',
        '🎧': '[HEADPHONES]',
        '🎵': '[MUSIC]',
        '🎶': '[NOTES]',
        '🎼': '[SCORE]',
        '🎹': '[PIANO]',
        '🥁': '[DRUM]',
        '🎷': '[SAX]',
        '🎺': '[TRUMPET]',
        '🎻': '[VIOLIN]',
        '🪗': '[ACCORDION]',
        '🪕': '[BANJO]',
        '🪘': '[LONG_DRUM]',
        '🎸': '[GUITAR]',
        '🪕': '[BANJO]',
        '🎺': '[TRUMPET]',
        '🎷': '[SAX]',
        '🥁': '[DRUM]',
        '🎹': '[PIANO]',
        '🎼': '[SCORE]',
        '🎶': '[NOTES]',
        '🎵': '[MUSIC]',
        '🎧': '[HEADPHONES]',
        '🎤': '[MIC]',
        '🎬': '[CLAPPER]',
        '🎨': '[ART]',
        '🎭': '[PERFORMING]',
        '🎪': '[CIRCUS]',
        '🎟️': '[ADMISSION]',
        '🎫': '[TICKET]',
        '🎗️': '[REMINDER]',
        '🏵️': '[ROSETTE]',
        '🎖️': '[MILITARY]',
        '🏆': '[TROPHY]',
        '🥉': '[BRONZE]',
        '🥈': '[SILVER]',
        '🥇': '[GOLD]',
        '🏅': '[MEDAL]',
        '🎀': '[RIBBON]',
        '🎁': '[GIFT]',
        '🎈': '[BALLOON]',
        '🎊': '[CONFETTI]',
        '✨': '[SPARKLES]',
        '💫': '[DIZZY]',
        '🌟': '[STAR_BRIGHT]',
        '⭐': '[STAR]',
        '🌙': '[MOON]',
        '☀️': '[SUN]',
        '🌈': '[RAINBOW]',
        '🌪️': '[TORNADO]',
        '🌊': '[WAVE]',
        '💧': '[WATER]',
        '🔥': '[FIRE]',
        '⚡': '[LIGHTNING]',
        '🔩': '[NUT]',
        '⚒️': '[PICKAXE]',
        '🔨': '[HAMMER]',
        '🛠️': '[TOOLS]',
        '⚙️': '[SETTINGS]',
        '🎯': '[TARGET]',
        '📍': '[LOCATION]',
        '📌': '[PIN]',
        '🔗': '[LINK]',
        '📂': '[FOLDER_OPEN]',
        '📁': '[FOLDER]',
        '📄': '[DOC]',
        '📧': '[EMAIL]',
        '🔓': '[UNLOCK]',
        '🔒': '[LOCK]',
        '💻': '[COMPUTER]',
        '🌐': '[WEB]',
        '📞': '[PHONE]',
        '🔍': '[SEARCH]',
        '⏰': '[TIME]'
    }
    
    original_content = content
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed Unicode in {filepath}")
        return True
    
    return False

def main():
    """Fix Unicode in all test files"""
    files_to_fix = [
        'test_credentials.py',
        'test_qr_code.py',
        'test_chatbot_integration.py',
        'test_performance.py',
        'performance_optimizer.py',
        'run_all_tests.py',
        'app.py'
    ]
    
    # Exclude CSS, JS, and HTML files
    files_to_fix = [f for f in files_to_fix if not f.endswith(('.css', '.js', '.html', '.htm'))]
    
    fixed_count = 0
    for filepath in files_to_fix:
        if fix_unicode_in_file(filepath):
            fixed_count += 1
    
    print(f"Fixed Unicode in {fixed_count} files")

if __name__ == "__main__":
    main()
