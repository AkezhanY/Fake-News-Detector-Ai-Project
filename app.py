from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    is_user = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Message('{self.content}', {self.is_user})"

class TrainingData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    is_fake = db.Column(db.Boolean, nullable=False)
    category = db.Column(db.String(100))
    source = db.Column(db.String(200))
    verified_by_human = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AnalysisLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.String(500), nullable=False)
    bot_response = db.Column(db.String(500))
    is_fake_prediction = db.Column(db.Boolean)
    confidence = db.Column(db.Float)
    user_feedback = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")
    
    # Add some initial training data if empty
    if TrainingData.query.count() == 0:
        print("📝 Adding initial training data...")
        initial_data = [
            TrainingData(
                text="Scientists discovered that drinking coffee cures all types of cancer instantly",
                is_fake=True,
                category="health",
                source="initial"
            ),
            TrainingData(
                text="Government is hiding evidence of alien civilizations visiting Earth",
                is_fake=True,
                category="conspiracy",
                source="initial"
            ),
            TrainingData(
                text="According to WHO data, vaccination reduces disease transmission by 60-80%",
                is_fake=False,
                category="health",
                source="initial"
            ),
            TrainingData(
                text="NASA confirms successful Mars rover landing and transmission of first images",
                is_fake=False,
                category="science",
                source="initial"
            )
        ]
        db.session.bulk_save_objects(initial_data)
        db.session.commit()
        print(f"✅ Added {len(initial_data)} initial training examples")

# IMPROVED fake news detection logic with training data integration
def analyze_news(text):
    text_lower = text.lower()
    
    print(f"🔍 Analyzing: {text}")
    
    # FIRST: Check if we have this exact text in training data
    existing_training = TrainingData.query.filter_by(text=text).first()
    if existing_training:
        print(f"🎯 EXACT MATCH in training data: {existing_training.is_fake}")
        confidence = 95
        if existing_training.is_fake:
            return {
                "is_fake": True,
                "confidence": confidence,
                "message": f"⚠️ Known Fake Content (confidence: {confidence}%)\n\nThis exact content has been verified as fake in our training database.",
                "score": 10,
                "source": "training_data"
            }
        else:
            return {
                "is_fake": False,
                "confidence": confidence,
                "message": f"✅ Verified Real Content (confidence: {confidence}%)\n\nThis exact content has been verified as reliable in our training database.",
                "score": 10,
                "source": "training_data"
            }
    
    # SECOND: Check for similar patterns in training data
    similar_training = TrainingData.query.filter(TrainingData.text.ilike(f"%{text}%")).first()
    if not similar_training:
        # Also check if training text is contained in user text
        all_training = TrainingData.query.all()
        for training_item in all_training:
            if training_item.text.lower() in text_lower:
                similar_training = training_item
                break
    
    if similar_training:
        print(f"🎯 SIMILAR MATCH in training data: {similar_training.is_fake}")
        confidence = 85
        if similar_training.is_fake:
            return {
                "is_fake": True,
                "confidence": confidence,
                "message": f"⚠️ Likely Fake Content (confidence: {confidence}%)\n\nThis content matches patterns previously identified as fake in our training database.",
                "score": 8,
                "source": "training_similar"
            }
        else:
            return {
                "is_fake": False,
                "confidence": confidence,
                "message": f"✅ Likely Real Content (confidence: {confidence}%)\n\nThis content matches patterns previously verified as reliable.",
                "score": 8,
                "source": "training_similar"
            }
    
    # THIRD: Rule-based detection for new content
    return rule_based_analysis(text)

def rule_based_analysis(text):
    text_lower = text.lower()
    
    # FORCE DETECTION patterns
    forced_fake_patterns = [
        'weather modification', 'chemtrails', 'government creating storms',
        'climate weapon', 'haarp', 'geoengineering'
    ]
    
    for pattern in forced_fake_patterns:
        if pattern in text_lower:
            print(f"🚨 FORCE DETECTED: {pattern}")
            return {
                "is_fake": True,
                "confidence": 90,
                "message": f"⚠️ Fake News Detected (confidence: 90%)\n\nThis matches known conspiracy theory patterns about '{pattern}'.",
                "score": 10,
                "source": "forced_pattern"
            }
    
    # Marketing scam patterns
    marketing_scam_patterns = [
        'does the work of', 'replaces all', 'one gadget that', 'but stores won\'t sell',
        'secret they don\'t want', 'banned by', 'doctors hate this', 'lose weight fast',
        'instant results', 'miracle', 'secret', 'hidden', 'they don\'t want you to know',
        'big companies hate', 'never before seen', 'revolutionary', 'groundbreaking',
        'overnight success', 'simple trick', 'one weird trick', 'one trick',
        'passive income', 'they don\'t want you', 'that they don\'t want you'
    ]
    
    for pattern in marketing_scam_patterns:
        if pattern in text_lower:
            print(f"🚨 MARKETING SCAM DETECTED: {pattern}")
            return {
                "is_fake": True,
                "confidence": 85,
                "message": f"⚠️ Marketing Scam Detected (confidence: 85%)\n\nThis appears to be exaggerated marketing claims or a potential scam.",
                "score": 10,
                "source": "marketing_pattern"
            }
    
    # Financial scam patterns
    financial_scam_patterns = [
        'make $', 'earn $', '$10000', '$10,000', 'weekly income', 'weekly earning',
        'make money from home', 'work from home', 'financial freedom', 'passive income',
        'get rich', 'become rich', 'money fast', 'easy money', 'quick money',
        'guaranteed income', 'millionaire', 'billionaire', 'cash fast',
        'no experience needed', 'no skills required', 'everyone can do it'
    ]
    
    for pattern in financial_scam_patterns:
        if pattern in text_lower:
            print(f"🚨 FINANCIAL SCAM DETECTED: {pattern}")
            return {
                "is_fake": True,
                "confidence": 90,
                "message": f"⚠️ Financial Scam Detected (confidence: 90%)\n\nThis shows clear signs of being a financial scam.",
                "score": 10,
                "source": "financial_pattern"
            }
    
    # Pattern-based detection with regex
    money_patterns = [
        r'\$\d+,\d+\s+weekly',
        r'\$\d+\s+weekly', 
        r'make\s+\$\d+',
        r'earn\s+\$\d+',
        r'\$\d+k?\s+per\s+week',
        r'\d+\s+dollars?\s+weekly'
    ]
    
    for pattern in money_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            print(f"🚨 MONEY PATTERN DETECTED: {pattern}")
            return {
                "is_fake": True,
                "confidence": 85,
                "message": "⚠️ Financial Scam Detected (confidence: 85%)\n\nThis contains patterns commonly used in financial scams.",
                "score": 10,
                "source": "regex_pattern"
            }
    
    # Expanded keywords for fake news
    fake_indicators = [
        # Financial scams
        'one trick', 'passive income', 'they don\'t want you to know', 'secret method',
        'get rich quick', 'easy money', 'guaranteed income', 'make money fast', 
        'work from home', 'financial freedom overnight', 'quick rich',
        # Marketing scams
        'does the work of', 'replaces all your', 'one gadget that', 'but stores won\'t sell',
        'secret they don\'t want', 'banned by', 'doctors hate this', 'lose weight fast',
        'instant results', 'miracle product', 'secret product', 'hidden gadget',
        'they don\'t want you to know', 'big companies hate', 'never before seen',
        'revolutionary product', 'groundbreaking invention', 'overnight success',
        'simple trick', 'one weird trick', 'this one trick',
        # Conspiracy theories
        'weather modification', 'chemtrails', 'government creating storms',
        'climate weapon', 'haarp', 'geoengineering',
        'shocking discovery', 'doctors are hiding', 'scientists in shock', 
        'government is hiding', 'they are hiding', 'secret method',
        'big pharma conspiracy', 'new world order', 'reptilians', 'illuminati',
        'government conspiracy', 'cover-up', 'suppressed truth',
        # General fake news patterns
        'they don\'t want you to know', 'mainstream media won\'t tell you', 
        'wake up people', 'the truth they hide', 'open your eyes'
    ]
    
    # Keywords for real news
    real_indicators = [
        'according to official data', 'research shows', 'experts confirm',
        'according to statistics', 'scientific study', 'official source',
        'verified information', 'peer-reviewed', 'clinical trial',
        'Reuters', 'Associated Press', 'BBC', 'CNN', 'NPR', 'AP News',
        'study published in', 'research from', 'data from',
        'according to experts', 'scientists say', 'medical professionals',
        'university research', 'clinical study', 'scientific evidence'
    ]
    
    fake_score = 0
    real_score = 0
    
    # Check for fake indicators
    for indicator in fake_indicators:
        if indicator in text_lower:
            fake_score += 3
            print(f"➕ Fake indicator found: '{indicator}'")
    
    # Check for real indicators  
    for indicator in real_indicators:
        if indicator in text_lower:
            real_score += 3
            print(f"➕ Real indicator found: '{indicator}'")
    
    # Additional pattern checks
    sensational_words = ['!!!', 'urgent!', 'must read', 'breaking news', 'shocking', 'amazing', 'incredible']
    if any(word in text_lower for word in sensational_words):
        fake_score += 2
    
    # Financial context detection
    financial_red_flags = ['make', 'earn', 'income', 'money', 'cash', 'paid', 'rich', 'wealth']
    financial_context = ['weekly', 'monthly', 'daily', 'from home', 'online', 'easy', 'simple', 'guaranteed', 'trick', 'secret']
    
    if any(word in text_lower for word in financial_red_flags) and any(word in text_lower for word in financial_context):
        fake_score += 3
    
    # Dollar amount detection
    if re.search(r'\$\d+', text):
        fake_score += 2
    
    if len(text) < 60:
        fake_score += 1
    
    if any(source in text for source in ['Reuters', 'AP', 'BBC', 'official', 'study', 'research', 'university']):
        real_score += 2
    
    print(f"📊 FINAL SCORES - Fake: {fake_score}, Real: {real_score}")
    
    # Determine result
    if fake_score >= 2:
        confidence = min(95, fake_score * 12)
        
        if any(word in text_lower for word in ['gadget', 'product', 'device']):
            message = f"⚠️ Marketing Exaggeration (confidence: {confidence}%)"
        elif any(word in text_lower for word in ['make', 'earn', 'money', 'income']):
            message = f"⚠️ Financial Scam (confidence: {confidence}%)"
        else:
            message = f"⚠️ Likely Fake News (confidence: {confidence}%)"
            
        return {
            "is_fake": True,
            "confidence": confidence,
            "message": message,
            "score": fake_score,
            "source": "rule_based"
        }
    elif real_score >= 2:
        confidence = min(95, real_score * 12)
        return {
            "is_fake": False,
            "confidence": confidence,
            "message": f"✅ Appears Reliable (confidence: {confidence}%)",
            "score": real_score,
            "source": "rule_based"
        }
    else:
        return {
            "is_fake": None,
            "confidence": 50,
            "message": "🤔 Cannot determine reliability. Please verify with official sources.",
            "score": 0,
            "source": "uncertain"
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_message():
    data = request.get_json()
    user_message = data.get('text', '')
    
    print(f"📨 Received message: {user_message}")
    
    # Analyze the message
    analysis_result = analyze_news(user_message)
    
    print(f"🎯 Analysis result: {analysis_result}")
    
    return jsonify({
        "result": analysis_result["message"],
        "is_fake": analysis_result["is_fake"],
        "confidence": analysis_result["confidence"],
        "source": analysis_result.get("source", "unknown")
    })

@app.route('/messages', methods=['GET'])
def get_messages():
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    return jsonify([{
        'content': message.content,
        'is_user': message.is_user,
        'timestamp': message.timestamp.isoformat() if message.timestamp else None
    } for message in messages])

@app.route('/messages', methods=['POST'])
def add_message():
    data = request.get_json()
    content = data.get('content')
    is_user = data.get('is_user', True)

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    new_message = Message(content=content, is_user=is_user)
    db.session.add(new_message)
    db.session.commit()

    return jsonify({'message': 'Message added successfully'}), 201

# Training routes
@app.route('/training')
def training_interface():
    return render_template('training.html')

@app.route('/training-data', methods=['GET', 'POST'])
def training_data():
    if request.method == 'GET':
        data = TrainingData.query.order_by(TrainingData.timestamp.desc()).all()
        return jsonify([{
            'id': item.id,
            'text': item.text,
            'is_fake': item.is_fake,
            'category': item.category,
            'source': item.source,
            'timestamp': item.timestamp.isoformat() if item.timestamp else None
        } for item in data])
    
    elif request.method == 'POST':
        data = request.get_json()
        new_item = TrainingData(
            text=data['text'],
            is_fake=data['is_fake'],
            category=data.get('category', 'general'),
            source=data.get('source', 'manual input')
        )
        db.session.add(new_item)
        db.session.commit()
        
        # Return the new item with ID
        return jsonify({
            'message': 'Data added successfully',
            'id': new_item.id
        })

@app.route('/training-data/<int:id>', methods=['DELETE'])
def delete_training_data(id):
    item = TrainingData.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Data deleted successfully'})

@app.route('/feedback', methods=['POST'])
def save_feedback():
    data = request.get_json()
    log = AnalysisLog(
        user_message=data['user_message'],
        bot_response=data.get('bot_response'),
        is_fake_prediction=data.get('is_fake'),
        confidence=data.get('confidence'),
        user_feedback=data.get('user_feedback')
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Feedback saved'})

@app.route('/retrain', methods=['POST'])
def retrain_model():
    try:
        # Count training data
        training_count = TrainingData.query.count()
        fake_count = TrainingData.query.filter_by(is_fake=True).count()
        real_count = TrainingData.query.filter_by(is_fake=False).count()
    
        return jsonify({
            "message": f"Training data updated! Total: {training_count} examples (Fake: {fake_count}, Real: {real_count})",
            "success": True,
            "stats": {
                "total": training_count,
                "fake": fake_count,
                "real": real_count
            }
        })
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}", "success": False}), 500

# Test function
def test_analysis():
    test_phrases = [
        "The One Trick to Earning Passive Income That They Don't Want You to Know",
        "Government weather modification program creating catastrophic storms",
        "This kitchen gadget does the work of 10 appliances - but stores won't sell it",
        "Make $10,000 weekly working from home",
        "According to NASA, climate change is real",
        "Reuters reports economic growth of 3% this quarter",
        "Earn $5,000 monthly with this simple online method",
        "Doctors hate this one simple weight loss trick"
    ]
    
    print("🧪 RUNNING TESTS...")
    for phrase in test_phrases:
        # Use rule-based analysis for tests to avoid database issues
        result = rule_based_analysis(phrase)
        status = "FAKE" if result['is_fake'] else "REAL" if result['is_fake'] is False else "UNKNOWN"
        print(f"Test: '{phrase}'")
        print(f"Result: {status} (confidence: {result['confidence']}%)")
        print(f"Source: {result.get('source', 'unknown')}")
        print("---")

if __name__ == "__main__":
    # Run tests when starting the server
    print("🚀 Starting Fake News Detector...")
    test_analysis()
    app.run(debug=True, host='0.0.0.0', port=5000)