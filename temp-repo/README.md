# Intelligents

## How to Run the Application

Follow these steps to get the application up and running:

### 1. Obtain VAPI Public Key

- Visit [vapi.ai](https://vapi.ai) and sign up for an account.
- Obtain your VAPI public key, which will be required for configuring the application.

### 2. Set Up and Run the Client

1. Open a terminal and navigate to the client directory:

   ```bash
   cd client
   npm install
   # Before running the application, make sure to add your VAPI key:
    # Open components/Dashboard.jsx
    # Replace the placeholder with your VAPI key on line 10.
   npm run start

2. Set Up and Run the Flask Backend

   ```bash
    cd flask-vapi-server
    python -m pip install -r requirements.txt
    python app.py

3. Open your browser and navigate to http://localhost:3000

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 011528303853.dkr.ecr.us-east-1.amazonaws.com
docker push 011528303853.dkr.ecr.us-east-1.amazonaws.com/colloquial-app:latest



