import streamlit as st
import json
import os
import requests
import random
from datetime import datetime
from twilio.rest import Client

TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]

DATA_FILE = 'complaints.json'
UPLOAD_FOLDER = 'uploaded_media'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def upload_image_to_internet(file_path):
    try:
        with open(file_path, "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {"key": IMGBB_API_KEY}
            files = {"image": file}
            response = requests.post(url, payload, files=files)
            if response.status_code == 200:
                return response.json()['data']['url']
            return None
    except Exception as e:
        return None

def send_whatsapp_message(to_number, text_message, media_urls_list=None):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        formatted_number = f"whatsapp:+91{to_number}" 
        
        message_data = {
            "from_": TWILIO_WHATSAPP_NUMBER,
            "body": text_message,
            "to": formatted_number
        }
        
        if media_urls_list and len(media_urls_list) > 0:
            message_data["media_url"] = media_urls_list 

        message = client.messages.create(**message_data)
        return True, message.sid
    except Exception as e:
        return False, str(e)

def generate_complaint_id():
    """Generates a random ID like CMP-123456"""
    return f"CMP-{random.randint(100000, 999999)}"

# ==========================================
# 3. STREAMLIT USER INTERFACE & NAVIGATION
# ==========================================
st.set_page_config(page_title="Complaint CRM", page_icon="🛠️", layout="wide")

# Sidebar for Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Kripya ek option chunein:", ["📝 Register Complaint", "🔍 Search & Update Status"])
st.sidebar.markdown("---")

# -----------------------------------------------------
# PAGE 1: REGISTER COMPLAINT
# -----------------------------------------------------
if menu == "📝 Register Complaint":
    st.title("🛠️ Register New Complaint")
    
    with st.form("complaint_form", clear_on_submit=True):
        st.subheader("Customer Details")
        name = st.text_input("Customer Name *")
        mobile = st.text_input("Customer Mobile Number (10 digits) *")
        address = st.text_area("Customer Address *")
        
        st.subheader("Complaint Details")
        issue = st.text_input("Kis chiz ki complaint hai? *")
        description = st.text_area("Detailed Problem")
        uploaded_files = st.file_uploader("Upload Complaint Photos", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        st.subheader("Service Man Details")
        serviceman_mobile = st.text_input("Service Man Mobile Number (10 digits) *")
        
        submit_btn = st.form_submit_button("Submit & Send WhatsApp")

    if submit_btn:
        if not name or not mobile or not address or not issue or not serviceman_mobile:
            st.error("Kripya sabhi mandatory (*) fields bharein!")
        else:
            complaint_id = generate_complaint_id()
            public_image_urls = []
            local_file_paths = []
            
            if uploaded_files:
                if len(uploaded_files) > 10:
                    st.warning("Maximum 10 photos ki limit hai. Pehli 10 process ho rahi hain.")
                    uploaded_files = uploaded_files[:10]

                with st.spinner('Photos upload ho rahi hain...'):
                    for file in uploaded_files:
                        local_path = os.path.join(UPLOAD_FOLDER, file.name)
                        with open(local_path, "wb") as f:
                            f.write(file.getbuffer())
                        local_file_paths.append(local_path)
                        
                        public_url = upload_image_to_internet(local_path)
                        if public_url:
                            public_image_urls.append(public_url)

            # Data me Status aur ID add kiya gaya hai
            complaint_data = {
                "id": complaint_id,
                "date": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
                "status": "Pending 🔴",  # Default status
                "name": name,
                "mobile": mobile,
                "address": address,
                "issue": issue,
                "description": description,
                "local_files": local_file_paths,
                "public_urls": public_image_urls,
                "serviceman_mobile": serviceman_mobile
            }
            
            with open(DATA_FILE, 'r+') as f:
                data = json.load(f)
                data.append(complaint_data)
                f.seek(0)
                json.dump(data, f, indent=4)
                
            st.success(f"✅ Complaint Registered! Your Complaint ID is: **{complaint_id}**")

            msg_body = f"""*New Complaint Registered* 🛠️
*Complaint ID:* {complaint_id}
*Name:* {name}
*Mobile:* {mobile}
*Address:* {address}
*Issue:* {issue}
*Details:* {description}
*Status:* Pending 🔴"""

            st.info("Sending WhatsApp Message...")
            serv_success, serv_response = send_whatsapp_message(
                serviceman_mobile, 
                f"🔔 *URGENT WORK ASSIGNED*\n\n{msg_body}", 
                public_image_urls
            )

            if serv_success:
                st.success("✅ Serviceman ko details bhej di gayi hain!")
            else:
                st.error(f"WhatsApp Error: {serv_response}")

# -----------------------------------------------------
# PAGE 2: SEARCH & UPDATE STATUS
# -----------------------------------------------------
elif menu == "🔍 Search & Update Status":
    st.title("🔍 Search Complaint")
    st.markdown("Customer ki **Complaint ID** daalkar uski details dekhein aur status update karein.")
    
    # Session state setup
    if 'search_result' not in st.session_state:
        st.session_state.search_result = None

    search_id = st.text_input("Enter Complaint ID (e.g., CMP-123456)")
    
    if st.button("Search"):
        if not search_id:
            st.warning("Kripya ID daalein.")
        else:
            # File read karke search karna
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            
            found = False
            for item in data:
                # ID match kar rahe hain (case-insensitive)
                if item.get('id', '').strip().upper() == search_id.strip().upper():
                    st.session_state.search_result = item
                    found = True
                    break
            
            if not found:
                st.session_state.search_result = None
                st.error(f"❌ '{search_id}' naam ki koi complaint nahi mili!")

    # Agar complaint mil gayi hai, tab ye section dikhega
    if st.session_state.search_result:
        comp = st.session_state.search_result
        
        st.markdown("---")
        st.subheader("📋 Complaint Details")
        
        # Display data in columns for better look
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Complaint ID:** {comp['id']}")
            st.write(f"**Date:** {comp['date']}")
            st.write(f"**Customer Name:** {comp['name']}")
            st.write(f"**Mobile:** {comp['mobile']}")
            st.write(f"**Address:** {comp['address']}")
        with col2:
            st.write(f"**Issue:** {comp['issue']}")
            st.write(f"**Description:** {comp['description']}")
            st.write(f"**Current Status:** {comp['status']}")
            
        # Status update karne ka dropdown
        st.markdown("### ⚙️ Update Status")
        
        # Determine current index for selectbox
        status_options = ["Pending 🔴", "Resolved ✅"]
        current_index = 0 if "Pending" in comp['status'] else 1
        
        new_status = st.selectbox("Is complaint ka naya status chunein:", status_options, index=current_index)
        
        if st.button("Update Status & Save"):
            # Update logic
            with open(DATA_FILE, 'r') as f:
                all_data = json.load(f)
            
            # Find the specific complaint and update its status
            for idx, item in enumerate(all_data):
                if item['id'] == comp['id']:
                    all_data[idx]['status'] = new_status
                    st.session_state.search_result['status'] = new_status # Update live screen
                    break
                    
            # Save back to JSON file
            with open(DATA_FILE, 'w') as f:
                json.dump(all_data, f, indent=4)
                
            st.success(f"✅ Complaint {comp['id']} ka status update karke **{new_status}** kar diya gaya hai!")