from supabase import create_client
import os

url = os.getenv("SUPABASE_URL", "https://owqtmdflhykxildcrpvc.supabase.co")
key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93cXRtZGZsaHlreGlsZGNycHZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMzMjc5MDUsImV4cCI6MjA5ODkwMzkwNX0.P8iTPSIuYfBJsZuV3UgGmrfpGP2p8aDnFH_NxtmTNjo")
supabase = create_client(url, key)
