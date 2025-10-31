import json
from pathlib import Path
from typing import Final

from CreateShorts.Data_Gen.create_audio import assemble_dialogue_pydub
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import generate_dialogue_audio
from CreateShorts.Data_Gen.subtitle_generator import SubtitleGenerator, SubtitleConfig
from CreateShorts.Data_Gen.formatter_script import generate_formatter_script_json
from CreateShorts.Prompt_Refinig_Service.refine_base_prompt import refine_base_prompt
from CreateShorts.theme_config import ThemeManager, ThemeConfig

MAX_TIME_LIMIT: Final[int] = 120

# Future update Skyreels.ai
# Crear configuración personalizada (opcional)

config = SubtitleConfig(
    fontsize=45,
    font='Arial-Bold',
    color='white',
    stroke_color='black',
    stroke_width=2
)


def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    return Path(__file__).parent.parent


def create_complete_short(topic: str, duration_seconds: int, theme: str = "default", use_template: bool = False,
                          is_monologue: bool = False, context_story: str = ""):
    """
    Creates a complete short video from start to finish.
    
    Args:
        topic (str): Topic for the video content
        duration_seconds (int): Desired duration in seconds
        theme (str): Theme name to use for video configuration
        use_template (bool): Whether to use a template
        :param context_story:
        :param topic:
        :param duration_seconds:
        :param theme:
        :param use_template:
        :param is_monologue:
    """

    print(f"-> Starting short video creation for topic: {topic}")
    print(f"-> Using theme: {theme}")

    # Load theme config
    theme_manager = ThemeManager()
    theme_config = theme_manager.get_theme_config(theme)

    script_prompt = refine_base_prompt(
        base_topic_or_idea=topic,
        theme_config=theme_config
    )

    if theme_config is None:
        print(f"Error: No se pudo cargar la configuración del tema '{theme}'")
        return

    print(f"-> Theme configuration loaded:")
    print(f"   Video path: {theme_config.video_path}")
    print(f"   Music path: {theme_config.music_path}")
    print(f"   Voice settings: {theme_config.voice_settings}")

    # 1. Generate the script here we need to validate if is it monologue or debate
    # if theme is horror or reddit, then we use monologue, else default (will change to debate).
    print("-> Generating script...")

    # if theme != "story_formatter":
    #     if is_monologue:
    #         script_json_input = generate_monolog_script_json(
    #             final_script_prompt=script_prompt,
    #             time_limit=duration_seconds,
    #             theme_config=theme_config,
    #             context=context_story
    #         )
    #
    #     else:
    #         script_json_input = generate_debate_script_json(
    #             topic=topic,
    #             time_limit=duration_seconds,
    #             theme_config=theme_config,
    #             use_template=use_template,
    #             context=context_story
    #         )

    def generate_audio_video(script_json_input: str, output_suffix: str = "_"):
        # 2. Generate audio chunks in memory
        print("-> Converting script to audio...")
        audio_chunks = generate_dialogue_audio(script_json_input, theme_config)

        if not audio_chunks:
            print("ERROR: Failed to generate audio chunks")
            return

        duration_sum = sum(a.duration for a in audio_chunks)
        duration_second = round(duration_sum)
        print(f"-> Duración total del audio: {duration_second} segundos")

        if duration_second > 200:
            print(f"⚠️ Advertencia: La duración ({duration_second:.2f}s) excede 120s")

        # 3. Assemble audio chunks
        print("-> Assembling audio chunks...")
        temp_audio_path = "temp_dialogue.mp3"
        final_audio_path = assemble_dialogue_pydub(audio_chunks, temp_audio_path)

        if not final_audio_path:
            print("ERROR: Failed to assemble audio")
            return

        try:
            subtitle_gen = SubtitleGenerator(config)
            subtitle_clips = subtitle_gen.create_subtitle_clips(audio_chunks)

            # 5. Create final video with everything
            project_root = get_project_root()
            create_final_video(
                voice_path=final_audio_path,
                music_path=theme_config.music_path,
                video_background_path=theme_config.video_path,
                output_path=str(project_root / "output" / f"{topic.replace(' ', '_').lower() + output_suffix}.mp4"),
                duration_sec=duration_second,
                subtitle_clips=subtitle_clips,
                background_volume=theme_config.music_volume
            )
        finally:
            from CreateShorts.Data_Gen.text_to_speach import clean_temp_audio
            clean_temp_audio()

    def get_script_lines_json_str(_part_data: dict) -> str:
        script_lines = _part_data.get('script_lines')
        if script_lines:
            return json.dumps(script_lines)
        return "[]"

    if theme == "story_formatter":
        # --- LÓGICA DE SERIE (Multi-Parte) ---

        json_series_str = generate_formatter_script_json(
            time_limit=duration_seconds,
            theme_config=theme_config,
            context_story=context_story
        )

        try:
            # multi_part_scripts_data es una LISTA DE DICCIONARIOS de Python
            multi_part_scripts_data = json.loads(json_series_str)

        except json.JSONDecodeError as e:
            print(f"Error fatal: El JSON devuelto por Gemini no es válido. {e}")
            return  # Abortar

        if not multi_part_scripts_data:
            print("ERROR: Falló la segmentación de la historia multiparte.")
            return

        # 2. ITERAR y RE-SERIALIZAR para la Fábrica
        for part_data in multi_part_scripts_data:
            part_number = part_data.get("part_number", 1)

            # 🚨 CORRECCIÓN CLAVE: Pasamos SÓLO las líneas, serializadas a string.
            single_script_json_str = get_script_lines_json_str(part_data)

            # Ejecutar el pipeline de un solo video para esta parte
            generate_audio_video(
                script_json_input=single_script_json_str,
                output_suffix=f"_part_{part_number}"
            )

    else:
        # --- LÓGICA DE VIDEO ÚNICO (Monólogo o Debate) ---

        if is_monologue:
            script_json_str = generate_monolog_script_json(
                final_script_prompt=script_prompt,
                time_limit=duration_seconds,
                theme_config=theme_config,
                context=context_story
            )
        else:
            script_json_str = generate_debate_script_json(
                topic=topic,
                time_limit=duration_seconds,
                theme_config=theme_config,
                use_template=use_template,
                context=context_story
            )

        generate_audio_video(script_json_input=script_json_str)


if __name__ == "__main__":
    # _context_story = """
    #  There is a lot of hype lately about AI tools, seems like the new gold fever, but how true is that?.
    #  AI tools definitively are a new way to generate income, either you are a programmer, a content creator, even an accountant if you like, you can use AI tools for everything.
    #  This, however, does not mean you will magically make money at the click of a button, you will need to think hard, work hard or and be creative.
    #  This video, for example, it does uses AI tools, but behind it there is a complicated algorithm that put it all together, there is hard work behind this video.
    #  You might think that is not really that impressive, and you are right, is not. However, the point is that because a lot of hard work behind it, it has been improving rapidly, and now it is capable to create very complex content with minimal effort.
    #  Nothing is for free and just remember that AI tools are not magic, it is your mind what makes the magic.
    #  Use AI tool, nothing wrong with that, but never forget that what you bring to the table is the most important part.
    # """
    _context_story = """
    Chapter 1: A Bunch of Brainless Idiots in A Play...
    
    “Because I love you.”
    
    
    The moment she heard those words, the puppet-like Lou Yaoyao completely collapsed. Tears began to fall like a broken string of pearls, unable to stop.
    
    
    Across the glass, Qin Zhi felt pain as he saw the tears fall from her eyes. He placed his hand on the glass window, wanting to wipe her tears, yet it was all but futile. In the end, he said with an aching heart: “Yaoyao, don’t cry.”
    
    
    But, how could she stop the tears? Lou Yaoyao cried until she almost fainted. Separated by the glass, Qin Zhi continued to console her in a gentle voice. That voice made her think back to a time where as long as she cried and make a scene, he would drop everything, no matter what it was, and come to accompany and coax her with that same gentle voice of his.
    
    
    She had been a fool to have believed that they had only had siblings affection. She had been a damn fool to have caused him take the blame for her.
    
    
    “Qin Zhi, why didn’t you tell me earlier?” Lou Yaoyao asked tearfully.
    
    
    Qin Zhi just smiled.
    
    
    He didn’t give her an answer as she knew what the answer was. Even if he told her, it would have been useless. Because at that time she had been obsessed with Chen Hao. In her eyes, there was no one else but Chen Hao.
    
    
    Having understood this, Lou Yaoyao cried more tears.
    
    
    The guard urged Lou Yaoyao away as the prison visiting hour was over.
    
    
    Qin Zhi called Lou Yaoyao.
    
    
    Lou Yaoyao held the receiver and leaned towards the glass crying and gasping for breath. She braced herself to hear what he had to say.
    
    
    Recupera tu presión 120/80 y limpia tus arterias ya
    Glycogen Plus
    Ads by Pubfuture
    
    “Yaoyao, I cannot be by your side to guard you anymore. You must take good care of yourself. Don’t be so willful anymore. Do you understand?”
    
    
    “Yes, yes.” Lou Yaoyao nodded absentmindedly.
    
    
    “Yaoyao...“
    
    
    “Yes, yes.”
    
    
    “Don’t marry Chen Hao. Find a man who will truly love you. When you do find him, be good to him, and live a good life, understand?”
    
    
    “Yes, yes.”
    
    
    Qin Zhi continued to speak endlessly. This was the first time in Lou Yaoyao’s entire life that she didn’t find his lecturing annoying. She earnestly responded, even though she didn’t hear a single word.
    
    
    The guard warned them to speed it up. Qin Zhi finally gave Lou Yaoyao a profound glance, put down the receiver, and finally got up to leave.
    
    
    Lou Yaoyao suddenly stood up and started hitting the window hard, despite the guard’s warning. She pointed at the receiver.
    
    
    Qin Zhi sounded an apology to the guard and, once again, picked up the receiver.
    
    
    Lou Yaoyao looked at Qin Zhi through the glass. This once handsome man had always paid attention to cleanliness, but after some short months, that man was no more. He had stubble that he seemed to have missed while shaving hastily. His face had become yellowish and unusually haggard, except his eyes. His eyes were still as brilliant as they were before. It seemed like the hardships of life had not affected him. As Lou Yaoyao looked, she felt a burst of sadness. Qin Zhi opened his mouth to hurry her up. Then, Lou Yaoyao said in unswerving arrogance, “Qin Zhi, you know that I am willful and selfish, therefore indulge me once again for the last time. Wait for me okay? I’m not asking you, I’m ordering you. You wait for me, or else don’t even think about having a good life after. You know that I can make one’s life a living hell!”
    
    
    She was always a vicious woman. Forcing people to do the things and never knowing how to repent, nevertheless, she was proud of it.
    
    
    At the beginning, Qin Zhi had not understood what she was speaking about. When he had figured it out, Lou Yaoyao had smiled, put down the receiver, and gone out.
    
    
    At first, Qin Zhi did not understand what she was saying. When he finally understood, Lou Yaoyao had smiled at him as she. He put down the receiver and walked away.
    
    
    After staring blankly at nothing for quite a while, Qin Zhi finally laughed. If she wanted him to wait, then he would wait. He resigned himself to the fact that in this lifetime, his life had fallen into this woman’s hand.
    
    Ads by Pubfuture
    Pubfuture Ads
    
    Lou Yaoyao cried for a long time until both her eyes were swollen like peaches. As she walked outside, the sunlight gave her a temporary blackout of vision.
    
    
    “Yaoyao.“
    
    
    Chen Hao, who was waiting outside, called out to her. He threw away the cigarette butt and smiled as he walks toward her.
    
    
    He wore a white shirt with a pair of white tailored trousers. His handsome and delicate face carried a faint smile. Walking in the sunlight, the golden ray behind him looked dazzling.
    
    
    Lou Yaoyao opened her eyes wide to face this man, she had looked at him many times, but this was the first time she seriously looked at him, thoroughly looked.
    
    
    Chen Hao reached for her hand, but Lou Yaoyao shook it off with disgust and walked straight to the side of the car.
    
    
    Chen Hao’s face stiffened but quickly resumed his smiling expression. He walked to the side of the car and considerately assisted her in opening the car door.
    
    
    Once Lou Yaoyao sat in, Chen Hao circled to the driver’s seat and started the car.
    
    
    Lou Yaoyao looked out of the window in a daze, as Chen Hao used the side mirror to look at her expression.
    
    
    Lou Yaoyao, looking impatient, turned her head, sneered and said, “Chen Hao, you must truly despise me? Right?”
    
    
    “Yaoyao, what kind of nonsense are you talking about?” Chen Hao was apparently surprised at what Lou Yaoyao had said as his face filled with astonishment. He turned his head to look at her with eyes overflowing with gentle helplessness. Eyes of a man who was helpless against the willfulness of his girlfriend.
    
    
    Lou Yaoyao, however, wasn’t deceived by him, so she minded her own business and said, “How can you not despise me. I killed your beloved woman and child. How can you not despise me?”
    
    
    Chen Hao knitted his brows and snarled: “Lou Yaoyao, what kind of nonsense are you talking about!”
    
    
    “I talk nonsense? You know what clearly happened. At the time, all three of us were there at the scene. You know how Lou Qingqing died, don’t you? The one who killed Lou Qingqing was me, not Qin Zhi.” After Lou Yaoyao said everything on her mind, she dropped another bombshell, “I’m going to turn myself in.”
    
    
    She had been muddle headed before, but after crying in the prison, her mind unexpectedly became very clear. She must not let Qin Zhi take the blame for her. Qin Zhi was now 32 years old, the prime of man’s lifetime. To serve ten years in prison in this rapidly progressing era meant that when he came out, the world would be like another universe.
    
    
    Although she was selfish, she would not let Qin Zhi ruin his whole life because of her. He deserved to have a much better life.
    
    
    Esta modelo tiene tantas curvas que fue reclutada por el FBI
    Herbeauty
    
    
    Chen Hao was shocked by what Lou Yaoyao had said and stared at her in surprise. He was in shock for quite a while. He looked earnestly at her and found that she was serious. His eyes flashed with a hint of fury, but soon put himself under control. Using a gentle voice, he said, “Yaoyao, we are going to get married next month. Don’t speak of this kind of nonsense. You and I are going to get married. Lou Qingqing and I are of no importance.”
    
    
    There won’t be a wedding.” Lou Yaoyao didn’t bother paying any attention to Chen Hao’s excuses. She mockingly said: “Aren’t you happy? You will finally get rid of me!”
    
    
    Chen Hao was enraged by her speech, with a look of affectionate and wounded, he said: “Lou Yaoyao, in the end, how can I convince you of my sincerity?”
    
    
    Lou Yaoyao just felt disgusted to the point of wanting to throw up, just not so long ago, she had —because of an argument with Lou Qingqing— accidentally killed Lou Qingqing as well as Lou Qingqing’s unborn child with her own hand, one corpse with two lives. However now, this man was actually talk about sincerity to the killer of his own child?
    
    
    Lou Yaoyao felt disgusted to the point of being nauseous. Not too long ago, she—because of an argument—had killed Lou Qingqing and Lou Qingqing’s unborn child by accident, one corpse with two lives. However, this man was seriously talking about sincerity to her, the killer of his own child?
    
    
    Lou Yaoyao suddenly felt sad for Lou Qingqing. They were sisters of the same father but different mothers. They had fought over such a disgusting man for more than ten years.
    
    
    Oh Lou Qingqing, if you were to look at this man now, would you crawl out of your grave?
    
    
    Perhaps... Chen Hao never loved Lou Qingqing?
    
    
    The more she thought, the more disgusted she was. Lou Yaoyao really didn’t want to look at this man’s face at the moment, “Stop the car!”
    
    
    How could Chen Hao stop the car? He looked over at her with his face still filled with great sadness, “Yaoyao, I know that you and Qin Zhe have always had a good relationship, so good in fact that it even makes me jealous. But that does not mean you can take the blame for Qin Zhe’s crime. I love you so much. Where do you place me in your heart? Have you ever even thought about my feeling?”
    
    
    Lou Yaoyao was dumbstruck. F***! She should have figured out a long ago that this man simply had a problem within his brain!
    
    
    “Stop talking. You make me feel disgusted! My brain must have been flooded with water to be in love with a man like you!” Lou Yaoyao was about to burst with rage. She looked at Chen Hao with hatred, “I will say it one more time. Stop the car!”
    
    
    Chen Hao, of course, would not stop the car. The fair and handsome face twisted with pain and was on the verge of tears: “Yaoyao...“
    
    
    Looking at Chen Hao’s face, Lou Yaoyao completely broke down, “Please stop talking. Whenever you open your mouth to talk, I just want to throw up!”
    
    
    Chen Hao seemed repulsed by the blunt remarks. Thus, he forgot his pretense and looked at her with wide eyes and a stiff face. He’d heard about Lou Yaoyao’s vicious mind and malicious speech. However, Lou Yaoyao had always been fond of him so, naturally, she would not speak to him with such foul language. Now he had just discovered that this woman had such a vulgar mouth.
    
    
    Lou Yaoyao was the kind of person that when she liked you, she would hold you up to the sky, but when she hated you, this woman would lose her mind!
    
    
    If she had been smart enough, she would not have had such a bitter falling-out at this time. If she had been smart enough, enough to endure patiently, she would not...
    
    
    The two of them were at a deadlock. Lou Yaoyao was not in the mood to look at him. Chen Hao took a few deep breaths and managed to calm himself down with great difficulty. He turned his head to show affection when the sound of a horn and the sudden screeching of brakes were heard.
    
    
    At the corner of the mountain road ahead, a heavy loaded truck crashed straight into them.
    
    
    The moment the steel reinforcement bar clashed against the forehead, time stopped. Twenty seven years of Lou Yaoyao’s life flashed before her eyes. An indescribable thought crossed her mind: This is such a tragic fairy tale with an extremely weird ending. Cinderella, the heroine, was stabbed to death by her vicious stepsister and then the fickle and heartless prince was about to live a happily ever after with her vicious stepsister. Unexpectedly, the prince and the stepsister were killed in a car accident. Furthermore, they died without a corpse intact! The situation was indeed a melodramatic (dog-blood) fairy tale!
    
    
    Before she closed her eyes, Lou Yaoyao thought of her unwillingness and regretted everything: Poor Qin Zhi, it seems that you will have to wait for me until the next life!
    """

    create_complete_short(
        topic="Top genshin DPS characters (and their best in slot support)",
        duration_seconds=75,
        theme="default",
        use_template=True,
        is_monologue=False,
        context_story=_context_story
    )
