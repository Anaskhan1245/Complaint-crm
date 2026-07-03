import streamlit as st
import json
import os
import random
from datetime import datetime

# ==========================================
# 0. INITIAL SETUP & MISSING VARIABLES
# ==========================================
DATA_FILE = "complaints.json"
UPLOAD_FOLDER = "uploaded_photos"

# Agar folder nahi hai toh bana lo
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Agar data file nahi hai toh empty list ke sath bana lo
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# Dummy Functions for Missing Logic (Yahan apni asli API daalein)
def upload_image_to_internet(local_path):
    return f"https://example.com/{os.path.basename(local_path)}"

def send_whatsapp_message(number, message, images=None):
    # Yahan apni Twilio/WhatsApp logic daalein
    return True, "Message sent successfully"

# ==========================================
# 1. HIDE STREAMLIT WATERMARKS
# ==========================================
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    [data-testid="stToolbar"] {visibility: hidden;}
    [data-testid="stBottomBlock"] {display: none;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR & ADMIN LOGIN
# ==========================================
def generate_complaint_id():
    return f"CMP-{random.randint(100000, 999999)}"

st.sidebar.title("⚙️ Admin Panel")
with st.sidebar.expander("🔐 Staff / Admin Login"):
    admin_pin = st.text_input("Enter PIN to unlock records", type="password")

is_admin = (admin_pin == "989761") 

if is_admin:
    st.sidebar.success("✅ Admin Access Granted")
    menu = st.sidebar.radio("Main Menu:", ["📝 Register Complaint", "🔍 Search & Update Status", "📊 View All Record"])
else:
    st.sidebar.info("Customer Mode: Sirf complaint darj kar sakte hain.")
    menu = "📝 Register Complaint"

# -----------------------------------------------------
# PAGE 1: REGISTER COMPLAINT (For Customers)
# -----------------------------------------------------
if menu == "📝 Register Complaint":
    st.title("🛠️ Register New Complaint")
    st.markdown("Apni problem yahan darj karein, humara serviceman aapse jaldi contact karega.")
    
    with st.form("complaint_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Aapka Naam (Customer Name) *")
            mobile = st.text_input("Aapka WhatsApp Number (10 digits) *")
        with col2:
            address = st.text_input("Pura Address (Full Address) *")
            issue = st.selectbox("Kya Problem Hai? (Select Issue) *", 
                                 ["Bed", "Almirah", "cooler", "Shoe Rack", "Office Table", "Dressing Table" ,"Chair", "Sofa set", "Other"])
            
        description = st.text_area("Problem ko detail me batayen (Description)")
        
        st.markdown("📸 **Photos (Optional - Max 10)**")
        uploaded_files = st.file_uploader("Kharab product ki photo upload karein", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        submit_btn = st.form_submit_button("Submit Complaint")
        
    if submit_btn:
        if not name or not mobile or not address or not issue:
            st.error("Kripya sabhi zaroori (*) fields bharein!")
        else:
            complaint_id = generate_complaint_id()
            public_image_urls = []
            local_file_paths = []
            
            if uploaded_files:
                if len(uploaded_files) > 10:
                    st.warning("Maximum 10 photos ki limit hai. Pehli 10 process ho rahi hain.")
                    uploaded_files = uploaded_files[:10]

                with st.spinner('Photos upload ho rahi hain, kripya pratiksha karein...'):
                    for file in uploaded_files:
                        local_path = os.path.join(UPLOAD_FOLDER, file.name)
                        with open(local_path, "wb") as f:
                            f.write(file.getbuffer())
                        local_file_paths.append(local_path)
                        
                        public_url = upload_image_to_internet(local_path)
                        if public_url:
                            public_image_urls.append(public_url)

            # ⚠️ YAHAN APNE SERVICEMAN KA NUMBER FIX KAR DEIN ⚠️
            fixed_serviceman_number = "9045447473" 
            
            complaint_data = {
                "id": complaint_id,
                "date": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
                "status": "Pending 🔴",
                "name": name,
                "mobile": mobile,
                "address": address,
                "issue": issue,
                "description": description,
                "local_files": local_file_paths,
                "public_urls": public_image_urls,
                "serviceman_mobile": fixed_serviceman_number
            }
            
            # FILE SAVE LOGIC FIXED
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                
            data.append(complaint_data)
            
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)
                
            st.success(f"✅ Complaint Registered! Aapki Complaint ID hai: **{complaint_id}**")
            st.info("System processing messages...")
            
            serv_msg_body = f"""*New Customer Complaint!* 🚨\n*ID:* {complaint_id}\n*Name:* {name}\n*Mobile:* {mobile}\n*Address:* {address}\n*Issue:* {issue}\n*Details:* {description}"""
            send_whatsapp_message(fixed_serviceman_number, serv_msg_body, public_image_urls)

            cust_msg_body = f"""Hello {name}, 👋\n\nAapki complaint mil gayi hai. 🛠️\n*Complaint ID:* {complaint_id}\n*Issue:* {issue}\n\nHumara serviceman jald hi aapse sampark karega. Dhanyawad!"""
            send_whatsapp_message(mobile, cust_msg_body)

# -----------------------------------------------------
# PAGE 2: SEARCH & UPDATE STATUS
# -----------------------------------------------------
elif menu == "🔍 Search & Update Status":
    st.title("🔍 Search & Manage Complaint")
    st.markdown("Customer ki **Complaint ID** daalkar uski details dekhein, status update karein, ya use delete karein.")
    
    if 'search_result' not in st.session_state:
        st.session_state.search_result = None

    search_id = st.text_input("Enter Complaint ID (e.g., CMP-123456)")
    
    if st.button("Search"):
        if not search_id:
            st.warning("Kripya ID daalein.")
        else:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            
            found = False
            for item in data:
                if item.get('id', '').strip().upper() == search_id.strip().upper():
                    st.session_state.search_result = item
                    found = True
                    break
            
            if not found:
                st.session_state.search_result = None
                st.error(f"❌ '{search_id}' naam ki koi complaint nahi mili!")

    if st.session_state.search_result:
        comp = st.session_state.search_result
        
        st.markdown("---")
        st.subheader("📋 Complaint Details")
        
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
            
        st.markdown("### ⚙️ Manage Complaint")
        
        status_options = ["Pending 🔴", "Resolved ✅"]
        current_index = 0 if "Pending" in comp.get('status', 'Pending 🔴') else 1
        
        new_status = st.selectbox("Is complaint ka naya status chunein:", status_options, index=current_index)
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("Update Status & Save"):
                with open(DATA_FILE, 'r') as f:
                    all_data = json.load(f)
                
                for idx, item in enumerate(all_data):
                    if item['id'] == comp['id']:
                        all_data[idx]['status'] = new_status
                        st.session_state.search_result['status'] = new_status 
                        break
                        
                with open(DATA_FILE, 'w') as f:
                    json.dump(all_data, f, indent=4)
                    
                st.success(f"✅ Complaint {comp['id']} ka status update karke **{new_status}** kar diya gaya hai!")

        with col4:
            if st.button("🗑️ Delete Complaint"):
                with open(DATA_FILE, 'r') as f:
                    all_data = json.load(f)
                
                updated_data = [item for item in all_data if item['id'] != comp['id']]
                
                with open(DATA_FILE, 'w') as f:
                    json.dump(updated_data, f, indent=4)
                    
                st.session_state.search_result = None
                st.success(f"🗑️ Complaint **{comp['id']}** hamesha ke liye delete ho gayi hai! Page refresh kar lein.")

# -----------------------------------------------------
# PAGE 3: VIEW ALL RECORDS
# -----------------------------------------------------
elif menu == "📊 View All Record":
    st.title("📊 All Complaints Record")
    st.markdown("Yahan aap saari registered complaints ek sath ek table me dekh sakte hain.")
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        
    if not data:
        st.info("Abhi tak koi complaint register nahi hui hai.")
    else:
        st.dataframe(data, use_container_width=True)
