import os

def ask_gemini(prompt):
    """
    Ask Gemini AI a question and return the response.
    
    Args:
        prompt (str): The user's question or prompt
        
    Returns:
        str: The AI's response or a fallback message if API call fails
    """
    try:
        # Try to import the required modules
        import google.generativeai as genai
        from flask import current_app
        
        # Get API key from environment variables
        api_key = os.environ.get('GOOGLE_API_KEY') or current_app.config.get('GEMINI_API_KEY')
        
        if not api_key:
            return "I'm sorry, but the AI service is not properly configured. Please contact support."
        
        # Configure the Gemini AI client
        genai.configure(api_key=api_key)
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Return the response text
        return response.text
        
    except ImportError as e:
        # Handle missing dependencies
        print(f"Missing dependencies for Gemini API: {e}")
        return "I'm sorry, but the AI service is not available due to missing dependencies."
    except Exception as e:
        # Handle API errors gracefully
        print(f"Error calling Gemini API: {e}")
        return "I'm sorry, but I'm having trouble accessing the AI service right now. Please try again later or contact support for assistance."