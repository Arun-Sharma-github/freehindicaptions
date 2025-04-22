from llm_code import generate_text
import os
from datetime import datetime


def convert_to_hinglish(srt_lines):
    try:
        # Save to custom output folder
        
        srt_data = "\n".join(srt_lines)
        output_dir = os.path.join(os.path.dirname(__file__), "srt_for_audio")
        os.makedirs(output_dir, exist_ok=True)  # Create folder if it doesn't exist
        
        today = datetime.now().strftime("%Y-%m-%d")  # Format: 2025-04-18
        srt_filename = f"{today}_yt.srt"
        
        full_srt_path = os.path.join(output_dir, srt_filename)

        
        
        
        # prompt_template= """ You are a hinglish expert your task is to convert the given SRT file data which will contain Hindi words into hinglish making same pronunciation as that in the Hindi form. Do not change the srt format like time duration and also the numbering. Just alter the Hindi words into english pronunciation the Hinglish form. Also do not give any other suggestion or explanation just the converted data and nothing else. """
        prompt_template= """ You are a hinglish expert your task is to convert the given SRT file data which will contain Hindi words into hinglish making same pronunciation as that in the Hindi form. Do not change the srt format like time duration and also the numbering. Just alter the Hindi words into english pronunciation the Hinglish form. Apart from this do not give anything in response.  Example: before 11
0:00:03,270 --> 0:00:03,660
हमेशा 
After conversion to hinglish:

11
0:00:03,270 --> 0:00:03,660
Hamesha


apart from this conversion format nothing else you will respond


"""
        final_prompt = prompt_template + srt_data
        # Call your LLM function
        generated_text = generate_text(final_prompt, max_tokens=2048)

        # Ensure it's a string (safety check, depends on how generate_text returns)
        if isinstance(generated_text, list):
            generated_text = "".join(generated_text)

        # Write to file properly
        with open(full_srt_path, "w", encoding="utf-8") as f:
            f.write(generated_text)

        print(f"Successfully converted to Hinglish")
        return full_srt_path
        
    except Exception as e:
        print(f"Error in conversion: {str(e)}")
        return None