import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      setToken(null);
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/login`, { username, password });
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      await fetchUser();
      return true;
    } catch (error) {
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      await axios.post(`${API}/register`, userData);
      return await login(userData.username, userData.password);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Login Component
const Login = ({ onSwitchToRegister }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(username, password);
    } catch (error) {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Government Schemes Portal</h1>
          <p className="text-gray-600 mt-2">Access welfare schemes for your family</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 font-medium"
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>
        
        <div className="text-center mt-6">
          <p className="text-gray-600">
            Don't have an account?{' '}
            <button
              onClick={onSwitchToRegister}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Register here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Register Component
const Register = ({ onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await register(formData);
    } catch (error) {
      setError(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Create Account</h1>
          <p className="text-gray-600 mt-2">Join the Government Schemes Portal</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 font-medium"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <div className="text-center mt-6">
          <p className="text-gray-600">
            Already have an account?{' '}
            <button
              onClick={onSwitchToLogin}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Sign in here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [family, setFamily] = useState(null);
  const [schemes, setSchemes] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchFamily();
    fetchSchemes();
    fetchNotifications();
  }, []);

  const fetchFamily = async () => {
    try {
      const response = await axios.get(`${API}/family`);
      setFamily(response.data);
    } catch (error) {
      console.error('Error fetching family:', error);
    }
  };

  const fetchSchemes = async () => {
    try {
      const response = await axios.get(`${API}/eligible-schemes`);
      setSchemes(response.data.schemes || []);
    } catch (error) {
      console.error('Error fetching schemes:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const checkEligibility = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/check-eligibility`);
      await fetchSchemes();
      await fetchNotifications();
    } catch (error) {
      console.error('Error checking eligibility:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyToScheme = async (schemeName) => {
    try {
      await axios.post(`${API}/apply-scheme/${schemeName}`);
      await fetchSchemes();
      await fetchNotifications();
    } catch (error) {
      console.error('Error applying to scheme:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Eligible': return 'bg-green-100 text-green-800';
      case 'Applied': return 'bg-blue-100 text-blue-800';
      case 'Approved': return 'bg-purple-100 text-purple-800';
      case 'Not Eligible': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Government Schemes Portal</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {user?.full_name}</span>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'profile', name: 'Family Profile', icon: '👨‍👩‍👧‍👦' },
              { id: 'schemes', name: 'Eligible Schemes', icon: '📋' },
              { id: 'notifications', name: 'Notifications', icon: '🔔' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Family Profile Tab */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            {!family ? (
              <FamilyRegistrationForm onComplete={fetchFamily} />
            ) : (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Family Profile</h2>
                  {!schemes.length && (
                    <button
                      onClick={checkEligibility}
                      disabled={loading}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
                    >
                      {loading ? 'Checking...' : 'Check Eligibility'}
                    </button>
                  )}
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-800">Head of Family</h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                      <p><strong>Name:</strong> {family.family_head_name}</p>
                      <p><strong>Age:</strong> {family.age} years</p>
                      <p><strong>Gender:</strong> {family.gender}</p>
                      <p><strong>Caste/Category:</strong> {family.caste_category}</p>
                      <p><strong>Occupation:</strong> {family.occupation}</p>
                      <p><strong>Annual Income:</strong> ₹{family.annual_income?.toLocaleString()}</p>
                      <p><strong>Education:</strong> {family.education_level}</p>
                      <p><strong>Disability:</strong> {family.disability ? 'Yes' : 'No'}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-800">Family Members ({family.family_members?.length || 0})</h3>
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {family.family_members?.map((member, index) => (
                        <div key={index} className="bg-gray-50 p-4 rounded-lg">
                          <p className="font-medium">{member.name}</p>
                          <p className="text-sm text-gray-600">
                            {member.age} years, {member.gender}, {member.relationship}
                          </p>
                          {member.occupation && (
                            <p className="text-sm text-gray-600">Occupation: {member.occupation}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Schemes Tab */}
        {activeTab === 'schemes' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Eligible Government Schemes</h2>
              
              {schemes.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No schemes analyzed yet.</p>
                  {family && (
                    <button
                      onClick={checkEligibility}
                      disabled={loading}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
                    >
                      {loading ? 'Checking Eligibility...' : 'Check Eligibility'}
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid gap-6">
                  {schemes.map((scheme, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-xl font-semibold text-gray-900">{scheme.scheme_name}</h3>
                          <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium mt-2 ${getStatusColor(scheme.status)}`}>
                            {scheme.status}
                          </span>
                        </div>
                        {scheme.status === 'Eligible' && (
                          <button
                            onClick={() => applyToScheme(scheme.scheme_name)}
                            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                          >
                            Apply Now
                          </button>
                        )}
                      </div>
                      
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-800 mb-2">AI Analysis:</h4>
                        <p className="text-gray-700 text-sm">{scheme.ai_reasoning}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === 'notifications' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Notifications</h2>
              
              {notifications.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No notifications yet.</p>
              ) : (
                <div className="space-y-4">
                  {notifications.map((notification, index) => (
                    <div key={index} className={`border-l-4 p-4 rounded-lg ${
                      notification.type === 'success' ? 'border-green-500 bg-green-50' :
                      notification.type === 'warning' ? 'border-yellow-500 bg-yellow-50' :
                      notification.type === 'error' ? 'border-red-500 bg-red-50' :
                      'border-blue-500 bg-blue-50'
                    }`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium text-gray-900">{notification.title}</h4>
                          <p className="text-gray-700 mt-1">{notification.message}</p>
                          <p className="text-gray-500 text-sm mt-2">
                            {new Date(notification.created_at).toLocaleString()}
                          </p>
                        </div>
                        {!notification.read && (
                          <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Family Registration Form Component
const FamilyRegistrationForm = ({ onComplete }) => {
  const [formData, setFormData] = useState({
    family_head_name: '',
    age: '',
    gender: '',
    caste_category: '',
    occupation: '',
    annual_income: '',
    education_level: '',
    disability: false,
    family_members: []
  });
  const [newMember, setNewMember] = useState({
    name: '',
    age: '',
    gender: '',
    relationship: '',
    education: '',
    occupation: '',
    disability: false
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleMemberChange = (e) => {
    const { name, value, type, checked } = e.target;
    setNewMember({
      ...newMember,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const addFamilyMember = () => {
    if (newMember.name && newMember.age && newMember.gender && newMember.relationship) {
      setFormData({
        ...formData,
        family_members: [...formData.family_members, { ...newMember, age: parseInt(newMember.age) }]
      });
      setNewMember({
        name: '',
        age: '',
        gender: '',
        relationship: '',
        education: '',
        occupation: '',
        disability: false
      });
    }
  };

  const removeFamilyMember = (index) => {
    setFormData({
      ...formData,
      family_members: formData.family_members.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const submitData = {
        ...formData,
        age: parseInt(formData.age),
        annual_income: parseFloat(formData.annual_income)
      };
      await axios.post(`${API}/family`, submitData);
      onComplete();
    } catch (error) {
      console.error('Error creating family profile:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Family Profile</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Head of Family */}
        <div className="border-b border-gray-200 pb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Head of Family</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Full Name *</label>
              <input
                type="text"
                name="family_head_name"
                value={formData.family_head_name}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Age *</label>
              <input
                type="number"
                name="age"
                value={formData.age}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Gender *</label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Caste/Category *</label>
              <select
                name="caste_category"
                value={formData.caste_category}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Category</option>
                <option value="SC">SC (Scheduled Caste)</option>
                <option value="ST">ST (Scheduled Tribe)</option>
                <option value="OBC">OBC (Other Backward Class)</option>
                <option value="General">General</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Occupation *</label>
              <input
                type="text"
                name="occupation"
                value={formData.occupation}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Farmer, Daily Labor, etc."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Annual Income (₹) *</label>
              <input
                type="number"
                name="annual_income"
                value={formData.annual_income}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Education Level *</label>
              <select
                name="education_level"
                value={formData.education_level}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Education</option>
                <option value="Illiterate">Illiterate</option>
                <option value="Primary">Primary (1-5)</option>
                <option value="Middle">Middle (6-8)</option>
                <option value="Secondary">Secondary (9-10)</option>
                <option value="Higher Secondary">Higher Secondary (11-12)</option>
                <option value="Graduate">Graduate</option>
                <option value="Post Graduate">Post Graduate</option>
              </select>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                name="disability"
                checked={formData.disability}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-700">Has Disability</label>
            </div>
          </div>
        </div>

        {/* Family Members */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Family Members</h3>
          
          {/* Add New Member */}
          <div className="bg-gray-50 p-4 rounded-lg mb-4">
            <h4 className="font-medium text-gray-700 mb-3">Add Family Member</h4>
            <div className="grid md:grid-cols-4 gap-3">
              <input
                type="text"
                name="name"
                placeholder="Name"
                value={newMember.name}
                onChange={handleMemberChange}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <input
                type="number"
                name="age"
                placeholder="Age"
                value={newMember.age}
                onChange={handleMemberChange}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <select
                name="gender"
                value={newMember.gender}
                onChange={handleMemberChange}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
              <input
                type="text"
                name="relationship"
                placeholder="Relationship"
                value={newMember.relationship}
                onChange={handleMemberChange}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="grid md:grid-cols-3 gap-3 mt-3">
              <input
                type="text"
                name="education"
                placeholder="Education (Optional)"
                value={newMember.education}
                onChange={handleMemberChange}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <input
                type="text"
                name="occupation"
                placeholder="Occupation (Optional)"
                value={newMember.occupation}
                onChange={handleMemberChange}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="disability"
                  checked={newMember.disability}
                  onChange={handleMemberChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">Has Disability</label>
              </div>
            </div>
            <button
              type="button"
              onClick={addFamilyMember}
              className="mt-3 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
            >
              Add Member
            </button>
          </div>

          {/* Existing Members */}
          {formData.family_members.length > 0 && (
            <div className="space-y-3">
              {formData.family_members.map((member, index) => (
                <div key={index} className="flex items-center justify-between bg-white border border-gray-200 p-3 rounded-lg">
                  <div>
                    <span className="font-medium">{member.name}</span>
                    <span className="text-gray-600 ml-2">
                      ({member.age} years, {member.gender}, {member.relationship})
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeFamilyMember(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 font-medium"
        >
          {loading ? 'Creating Profile...' : 'Create Family Profile'}
        </button>
      </form>
    </div>
  );
};

// Main App Component
function App() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <AuthProvider>
      <AppContent isLogin={isLogin} setIsLogin={setIsLogin} />
    </AuthProvider>
  );
}

const AppContent = ({ isLogin, setIsLogin }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return isLogin ? (
      <Login onSwitchToRegister={() => setIsLogin(false)} />
    ) : (
      <Register onSwitchToLogin={() => setIsLogin(true)} />
    );
  }

  return <Dashboard />;
};

export default App;