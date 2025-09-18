# Script to fix the syntax error in chatbot_service.py
with open(r'c:\Users\shahj\OneDrive\Desktop\Stadium System\app\services\chatbot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken line
fixed_content = content.replace("any(word in message_lower for \n word", "any(word in message_lower for word")

# Write the fixed content back to the file
with open(r'c:\Users\shahj\OneDrive\Desktop\Stadium System\app\services\chatbot_service.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("✅ Fixed the syntax error in chatbot_service.py")