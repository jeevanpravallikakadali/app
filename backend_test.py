#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Government Scheme Application Portal
Tests all backend APIs including authentication, family registration, AI eligibility, and notifications
"""

import requests
import json
import os
import time
from pathlib import Path

# Configuration
BASE_URL = "https://schemefinder-2.preview.emergentagent.com/api"
TEST_USER_DATA = {
    "email": "rajesh.kumar@gmail.com",
    "username": "rajesh_kumar",
    "full_name": "Rajesh Kumar Singh",
    "password": "SecurePass123!"
}

TEST_FAMILY_DATA = {
    "family_head_name": "Rajesh Kumar Singh",
    "age": 45,
    "gender": "Male",
    "caste_category": "OBC",
    "occupation": "Farmer",
    "annual_income": 85000.0,
    "education_level": "Class 10",
    "disability": False,
    "family_members": [
        {
            "name": "Sunita Singh",
            "age": 40,
            "gender": "Female",
            "relationship": "Wife",
            "education": "Class 8",
            "occupation": "Homemaker",
            "disability": False
        },
        {
            "name": "Amit Kumar Singh",
            "age": 18,
            "gender": "Male",
            "relationship": "Son",
            "education": "Class 12",
            "occupation": "Student",
            "disability": False
        },
        {
            "name": "Priya Singh",
            "age": 15,
            "gender": "Female",
            "relationship": "Daughter",
            "education": "Class 9",
            "occupation": "Student",
            "disability": False
        }
    ]
}

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {}
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "details": details
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            response = self.session.post(f"{BASE_URL}/register", json=TEST_USER_DATA)
            
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('email') == TEST_USER_DATA['email']:
                    self.log_test("User Registration", True, "User registered successfully")
                    return True
                else:
                    self.log_test("User Registration", False, "Invalid response data", user_data)
                    return False
            elif response.status_code == 400 and "already exists" in response.text:
                self.log_test("User Registration", True, "User already exists (expected for repeat tests)")
                return True
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login and JWT token generation"""
        try:
            login_data = {
                "username": TEST_USER_DATA["username"],
                "password": TEST_USER_DATA["password"]
            }
            response = self.session.post(f"{BASE_URL}/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                if token_data.get('access_token') and token_data.get('token_type') == 'bearer':
                    self.auth_token = token_data['access_token']
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    self.log_test("User Login", True, "Login successful, JWT token received")
                    return True
                else:
                    self.log_test("User Login", False, "Invalid token response", token_data)
                    return False
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_current_user(self):
        """Test getting current user info with JWT"""
        try:
            response = self.session.get(f"{BASE_URL}/me")
            
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('username') == TEST_USER_DATA['username']:
                    self.log_test("Get Current User", True, "User info retrieved successfully")
                    return True
                else:
                    self.log_test("Get Current User", False, "Invalid user data", user_data)
                    return False
            else:
                self.log_test("Get Current User", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Get Current User", False, f"Request failed: {str(e)}")
            return False
    
    def test_family_creation(self):
        """Test family profile creation"""
        try:
            response = self.session.post(f"{BASE_URL}/family", json=TEST_FAMILY_DATA)
            
            if response.status_code == 200:
                family_data = response.json()
                if family_data.get('family_head_name') == TEST_FAMILY_DATA['family_head_name']:
                    self.log_test("Family Creation", True, "Family profile created successfully")
                    return True
                else:
                    self.log_test("Family Creation", False, "Invalid family data", family_data)
                    return False
            else:
                self.log_test("Family Creation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Family Creation", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_family(self):
        """Test retrieving family profile"""
        try:
            response = self.session.get(f"{BASE_URL}/family")
            
            if response.status_code == 200:
                family_data = response.json()
                if family_data and family_data.get('family_head_name') == TEST_FAMILY_DATA['family_head_name']:
                    self.log_test("Get Family", True, "Family profile retrieved successfully")
                    return True
                elif family_data is None:
                    self.log_test("Get Family", False, "No family profile found")
                    return False
                else:
                    self.log_test("Get Family", False, "Invalid family data", family_data)
                    return False
            else:
                self.log_test("Get Family", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Get Family", False, f"Request failed: {str(e)}")
            return False
    
    def test_document_upload(self):
        """Test document upload functionality"""
        try:
            # Create a test document file
            test_content = "This is a test Aadhaar card document for Rajesh Kumar Singh"
            
            files = {
                'file': ('aadhaar_card.txt', test_content, 'text/plain')
            }
            data = {
                'document_type': 'aadhaar_card'
            }
            
            response = self.session.post(f"{BASE_URL}/upload-document", files=files, data=data)
            
            if response.status_code == 200:
                upload_data = response.json()
                if upload_data.get('filename') and upload_data.get('message'):
                    self.log_test("Document Upload", True, "Document uploaded successfully")
                    return True
                else:
                    self.log_test("Document Upload", False, "Invalid upload response", upload_data)
                    return False
            else:
                self.log_test("Document Upload", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Document Upload", False, f"Request failed: {str(e)}")
            return False
    
    def test_ai_eligibility_check(self):
        """Test AI-powered scheme eligibility checking"""
        try:
            response = self.session.post(f"{BASE_URL}/check-eligibility")
            
            if response.status_code == 200:
                eligibility_data = response.json()
                schemes = eligibility_data.get('schemes', [])
                
                if len(schemes) > 0:
                    # Check if we have the expected schemes
                    scheme_names = [scheme.get('scheme_name') for scheme in schemes]
                    expected_schemes = ["PM-KISAN", "MGNREGA", "PM-JAY", "PMAY-Gramin", "Jan Aushadhi"]
                    
                    if all(scheme in scheme_names for scheme in expected_schemes):
                        eligible_count = len([s for s in schemes if s.get('status') == 'Eligible'])
                        self.log_test("AI Eligibility Check", True, 
                                    f"Eligibility check completed. {eligible_count} eligible schemes found")
                        return True
                    else:
                        self.log_test("AI Eligibility Check", False, 
                                    f"Missing expected schemes. Found: {scheme_names}")
                        return False
                else:
                    self.log_test("AI Eligibility Check", False, "No schemes returned", eligibility_data)
                    return False
            else:
                self.log_test("AI Eligibility Check", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("AI Eligibility Check", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_eligible_schemes(self):
        """Test retrieving eligible schemes"""
        try:
            response = self.session.get(f"{BASE_URL}/eligible-schemes")
            
            if response.status_code == 200:
                schemes_data = response.json()
                schemes = schemes_data.get('schemes', [])
                
                if len(schemes) > 0:
                    self.log_test("Get Eligible Schemes", True, f"Retrieved {len(schemes)} scheme records")
                    return True
                else:
                    self.log_test("Get Eligible Schemes", False, "No schemes found")
                    return False
            else:
                self.log_test("Get Eligible Schemes", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Get Eligible Schemes", False, f"Request failed: {str(e)}")
            return False
    
    def test_scheme_application(self):
        """Test applying to a scheme"""
        try:
            # First get eligible schemes to find one to apply to
            response = self.session.get(f"{BASE_URL}/eligible-schemes")
            if response.status_code != 200:
                self.log_test("Scheme Application", False, "Could not get schemes to apply to")
                return False
            
            schemes = response.json().get('schemes', [])
            eligible_schemes = [s for s in schemes if s.get('status') == 'Eligible']
            
            if not eligible_schemes:
                self.log_test("Scheme Application", False, "No eligible schemes to apply to")
                return False
            
            # Apply to the first eligible scheme
            scheme_name = eligible_schemes[0]['scheme_name']
            response = self.session.post(f"{BASE_URL}/apply-scheme/{scheme_name}")
            
            if response.status_code == 200:
                apply_data = response.json()
                if apply_data.get('message'):
                    self.log_test("Scheme Application", True, f"Successfully applied to {scheme_name}")
                    return True
                else:
                    self.log_test("Scheme Application", False, "Invalid application response", apply_data)
                    return False
            else:
                self.log_test("Scheme Application", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Scheme Application", False, f"Request failed: {str(e)}")
            return False
    
    def test_notifications(self):
        """Test notifications system"""
        try:
            response = self.session.get(f"{BASE_URL}/notifications")
            
            if response.status_code == 200:
                notifications_data = response.json()
                notifications = notifications_data.get('notifications', [])
                
                if len(notifications) > 0:
                    # Test marking a notification as read
                    first_notification = notifications[0]
                    notification_id = first_notification.get('id')
                    
                    if notification_id:
                        read_response = self.session.put(f"{BASE_URL}/notifications/{notification_id}/read")
                        if read_response.status_code == 200:
                            self.log_test("Notifications System", True, 
                                        f"Retrieved {len(notifications)} notifications and marked one as read")
                            return True
                        else:
                            self.log_test("Notifications System", False, 
                                        f"Could not mark notification as read: {read_response.status_code}")
                            return False
                    else:
                        self.log_test("Notifications System", True, 
                                    f"Retrieved {len(notifications)} notifications (no ID to test read)")
                        return True
                else:
                    self.log_test("Notifications System", True, "No notifications found (expected for new user)")
                    return True
            else:
                self.log_test("Notifications System", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Notifications System", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests in sequence"""
        print("🚀 Starting Government Scheme Portal Backend Tests")
        print(f"🌐 Testing against: {BASE_URL}")
        print("=" * 60)
        
        # Test sequence - order matters for dependencies
        tests = [
            ("User Authentication", [
                self.test_user_registration,
                self.test_user_login,
                self.test_get_current_user
            ]),
            ("Family Management", [
                self.test_family_creation,
                self.test_get_family
            ]),
            ("Document Upload", [
                self.test_document_upload
            ]),
            ("AI Eligibility Engine", [
                self.test_ai_eligibility_check,
                self.test_get_eligible_schemes
            ]),
            ("Scheme Applications", [
                self.test_scheme_application
            ]),
            ("Notifications", [
                self.test_notifications
            ])
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for category, test_functions in tests:
            print(f"\n📋 Testing {category}:")
            for test_func in test_functions:
                total_tests += 1
                if test_func():
                    passed_tests += 1
                time.sleep(0.5)  # Small delay between tests
        
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Backend is working correctly.")
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed. Check the details above.")
        
        return self.test_results

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Print detailed results
    print("\n📝 Detailed Test Results:")
    for test_name, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {test_name}: {result['message']}")