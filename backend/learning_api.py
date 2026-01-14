"""
Backend API Endpoints for Continuous Learning System

Provides REST API endpoints for:
- Patient learning data collection
- Feedback submission
- Learning insights and analytics
- Model performance tracking
"""

from flask import Flask, request, jsonify
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.learning.patient_learning_system import (
    get_learning_system, add_patient_learning_data, add_learning_feedback,
    get_patient_learning_insights, get_global_learning_insights
)

app = Flask(__name__)

@app.route('/api/learning/data/<patient_id>', methods=['POST'])
def add_learning_data(patient_id):
    """Add learning data point for patient."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['features', 'detection_result', 'confidence']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Add learning data
        data_point_id = add_patient_learning_data(
            patient_id=patient_id,
            features=data['features'],
            detection_result=data['detection_result'],
            confidence=data['confidence'],
            actual_outcome=data.get('actual_outcome')
        )
        
        if data_point_id:
            return jsonify({
                'success': True,
                'data_point_id': data_point_id,
                'message': 'Learning data added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add learning data'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learning/feedback/<patient_id>', methods=['POST'])
def add_feedback_endpoint(patient_id):
    """Add feedback for learning improvement."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['data_point_id', 'actual_outcome', 'correct']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Add feedback
        success = add_learning_feedback(
            patient_id=patient_id,
            data_point_id=data['data_point_id'],
            actual_outcome=data['actual_outcome'],
            correct=data['correct']
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Feedback added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add feedback'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learning/insights/<patient_id>', methods=['GET'])
def get_patient_insights_endpoint(patient_id):
    """Get learning insights for specific patient."""
    try:
        insights = get_patient_learning_insights(patient_id)
        
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'insights': insights,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learning/insights/global', methods=['GET'])
def get_global_insights_endpoint():
    """Get global learning insights."""
    try:
        insights = get_global_learning_insights()
        
        return jsonify({
            'success': True,
            'insights': insights,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learning/models/<patient_id>', methods=['GET'])
def get_patient_model(patient_id):
    """Get patient-specific model information."""
    try:
        learning_system = get_learning_system()
        if not learning_system:
            return jsonify({
                'success': False,
                'error': 'Learning system not initialized'
            }), 500
        
        # Get patient model if available
        if patient_id in learning_system.patient_models:
            model = learning_system.patient_models[patient_id]
            return jsonify({
                'success': True,
                'patient_id': patient_id,
                'model': {
                    'threshold': model.get('threshold', 0.5),
                    'feature_weights': model.get('feature_weights', {}),
                    'last_updated': datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                'success': True,
                'patient_id': patient_id,
                'model': None,
                'message': 'No model available for this patient'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learning/performance/<patient_id>', methods=['GET'])
def get_patient_performance(patient_id):
    """Get patient model performance metrics."""
    try:
        learning_system = get_learning_system()
        if not learning_system:
            return jsonify({
                'success': False,
                'error': 'Learning system not initialized'
            }), 500
        
        # Get performance metrics
        if patient_id in learning_system.patient_performance:
            perf = learning_system.patient_performance[patient_id]
            return jsonify({
                'success': True,
                'patient_id': patient_id,
                'performance': {
                    'accuracy': perf.accuracy,
                    'precision': perf.precision,
                    'recall': perf.recall,
                    'false_positive_rate': perf.false_positive_rate,
                    'false_negative_rate': perf.false_negative_rate,
                    'total_predictions': perf.total_predictions,
                    'last_updated': datetime.fromtimestamp(perf.last_updated).isoformat()
                }
            })
        else:
            return jsonify({
                'success': True,
                'patient_id': patient_id,
                'performance': None,
                'message': 'No performance data available'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learning/retrain/<patient_id>', methods=['POST'])
def trigger_retrain(patient_id):
    """Trigger manual model retraining for patient."""
    try:
        learning_system = get_learning_system()
        if not learning_system:
            return jsonify({
                'success': False,
                'error': 'Learning system not initialized'
            }), 500
        
        # Trigger retraining
        if learning_system._should_retrain_model(patient_id):
            learning_system._retrain_patient_model(patient_id)
            return jsonify({
                'success': True,
                'message': f'Model retraining triggered for patient {patient_id}'
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Insufficient data for retraining patient {patient_id}'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learning/status', methods=['GET'])
def get_learning_status():
    """Get overall learning system status."""
    try:
        learning_system = get_learning_system()
        if not learning_system:
            return jsonify({
                'success': False,
                'error': 'Learning system not initialized'
            }), 500
        
        status = {
            'total_patients': len(learning_system.patient_data),
            'total_data_points': len(learning_system.global_training_data),
            'models_trained': len(learning_system.patient_models),
            'feature_importance': dict(sorted(
                learning_system.feature_importance.items(),
                key=lambda x: x[1], reverse=True
            )[:10]),
            'patients_with_performance': len(learning_system.patient_performance)
        }
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learning/export/<patient_id>', methods=['GET'])
def export_patient_data(patient_id):
    """Export patient learning data for analysis."""
    try:
        learning_system = get_learning_system()
        if not learning_system:
            return jsonify({
                'success': False,
                'error': 'Learning system not initialized'
            }), 500
        
        if patient_id not in learning_system.patient_data:
            return jsonify({
                'success': False,
                'error': f'No data found for patient {patient_id}'
            }), 404
        
        # Export patient data
        patient_data = list(learning_system.patient_data[patient_id])
        export_data = []
        
        for dp in patient_data:
            export_data.append({
                'timestamp': datetime.fromtimestamp(dp.timestamp).isoformat(),
                'features': dp.features,
                'detection_result': dp.detection_result,
                'actual_outcome': dp.actual_outcome,
                'confidence': dp.confidence,
                'feedback_received': dp.feedback_received
            })
        
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'export_data': export_data,
            'total_records': len(export_data),
            'export_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🧠 Starting Learning System API...")
    app.run(host='0.0.0.0', port=5001, debug=True)
