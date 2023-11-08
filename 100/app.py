import streamlit as st
import os
import openai

openai.api_key = os.environ['OPENAI_API_KEY']


def main():
    st.set_page_config(page_title="Image Generation Demo", page_icon=":robot_face:", layout="wide")
    st.title("Image Generation Demo")

    menu = ["Generation", "Generation Detailed"]
    choice = st.sidebar.selectbox("Select an option", menu)

    if choice == "Generation":
        text = st.text_input("Enter text")
        # num_images = st.number_input("Number of images", min_value=1, max_value=4, value=1, step=1)
        num_images=1
        resolution = st.multiselect("Choose Resolution", ['1024x1024', '1024x1792', '1792x1024'], default="1024x1024")[0]
        quality = st.multiselect("Choose Quality", ['standard', 'hd'], default="standard")[0]
        
        response = openai.Image.create(
                    model="dall-e-3",
                    prompt=text,
                    n=num_images, 
                    size=resolution,
                    quality=quality
                    )


        images = response['data']

        st.markdown(f"**new prompt** \n \\ {images[0]['revised_prompt']}")

        st.image(images[0]['url'])

        if st.download_button(label="Download", data=images[0]['url'], file_name=f"demo_images/{text}.png", mime="image/png"):
            st.write("Downloaded")

    elif choice == "Generation Detailed":
        company_name = st.text_input("Enter Company Name")
        industry = st.text_input("Enter Industry")
        description = st.text_input("Enter Description")

        num_images=1
        resolution = st.multiselect("Choose Resolution", ['1024x1024', '1024x1792', '1792x1024'], default="1024x1024")[0]
        quality = st.multiselect("Choose Quality", ['standard', 'hd'], default="standard")[0]
        
        prompt = f"PowerPoint presentation cover image for company with name {company_name} from {industry} industry professional\n\n{description}"
        
        st.write(prompt)
        
        if company_name and industry and description:
            response = openai.Image.create(
                        model="dall-e-3",
                        prompt=prompt,
                        n=num_images, 
                        size=resolution,
                        quality=quality
                        )
            
            
            images = response['data']

            st.markdown(f"**new prompt** \n \\ {images[0]['revised_prompt']}")

            st.image(images[0]['url'])

            if st.download_button(label="Download", data=images[0]['url'], file_name=f"demo_images/{prompt}.png", mime="image/png"):
                st.write("Downloaded")


if __name__ == "__main__":
    main()


