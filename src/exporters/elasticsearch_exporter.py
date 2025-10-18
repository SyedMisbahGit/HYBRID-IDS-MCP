#!/usr/bin/env python3
"""
Elasticsearch Exporter for Hybrid IDS
Sends alerts and features directly to Elasticsearch for real-time dashboarding
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False
    logging.warning("elasticsearch package not installed. Install with: pip install elasticsearch")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ElasticsearchExporter:
    """
    Exports Hybrid IDS data to Elasticsearch for visualization in Kibana
    """

    def __init__(self, hosts: List[str] = None, index_prefix: str = "hybrid-ids"):
        """
        Initialize Elasticsearch exporter

        Args:
            hosts: List of Elasticsearch hosts (default: ['http://localhost:9200'])
            index_prefix: Prefix for index names (default: 'hybrid-ids')
        """
        if not ES_AVAILABLE:
            raise ImportError("elasticsearch package required. Install with: pip install elasticsearch")

        self.hosts = hosts or ['http://localhost:9200']
        self.index_prefix = index_prefix
        self.es = None
        self.stats = {
            'nids_alerts_sent': 0,
            'ai_alerts_sent': 0,
            'features_sent': 0,
            'errors': 0
        }

    def connect(self) -> bool:
        """
        Connect to Elasticsearch

        Returns:
            True if successful
        """
        try:
            logger.info(f"Connecting to Elasticsearch at {self.hosts}...")
            self.es = Elasticsearch(hosts=self.hosts)

            # Test connection
            if self.es.ping():
                info = self.es.info()
                logger.info(f"Connected to Elasticsearch {info['version']['number']}")
                return True
            else:
                logger.error("Failed to ping Elasticsearch")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            return False

    def create_index_templates(self):
        """Create index templates for better performance and mapping"""

        # NIDS Alerts template
        nids_template = {
            "index_patterns": [f"{self.index_prefix}-nids-alerts-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "severity": {"type": "keyword"},
                        "severity_level": {"type": "integer"},
                        "rule_id": {"type": "integer"},
                        "message": {"type": "text"},
                        "src_ip": {"type": "ip"},
                        "dst_ip": {"type": "ip"},
                        "src_port": {"type": "integer"},
                        "dst_port": {"type": "integer"},
                        "protocol": {"type": "keyword"},
                        "source.geo.location": {"type": "geo_point"},
                        "destination.geo.location": {"type": "geo_point"},
                        "threat.technique.name": {"type": "keyword"},
                        "threat.tactic.name": {"type": "keyword"}
                    }
                }
            }
        }

        # AI Alerts template
        ai_template = {
            "index_patterns": [f"{self.index_prefix}-ai-alerts-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "confidence": {"type": "float"},
                        "risk_level": {"type": "keyword"},
                        "threat.score": {"type": "integer"},
                        "ml.ensemble_score": {"type": "float"},
                        "ml.models.random_forest": {"type": "float"},
                        "ml.models.isolation_forest": {"type": "float"},
                        "performance.inference_ms": {"type": "float"}
                    }
                }
            }
        }

        # Network Features template
        features_template = {
            "index_patterns": [f"{self.index_prefix}-network-features-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "duration": {"type": "float"},
                        "total_fwd_packets": {"type": "integer"},
                        "total_bwd_packets": {"type": "integer"},
                        "total_packets": {"type": "integer"},
                        "total_fwd_bytes": {"type": "long"},
                        "total_bwd_bytes": {"type": "long"},
                        "total_bytes": {"type": "long"},
                        "flow_bytes_per_sec": {"type": "float"},
                        "flow_packets_per_sec": {"type": "float"},
                        "syn_flag_count": {"type": "integer"},
                        "fin_flag_count": {"type": "integer"},
                        "rst_flag_count": {"type": "integer"},
                        "flow_type": {"type": "keyword"},
                        "traffic_category": {"type": "keyword"}
                    }
                }
            }
        }

        try:
            # Create templates (Elasticsearch 8.x uses _index_template API)
            self.es.indices.put_index_template(name=f"{self.index_prefix}-nids", body=nids_template)
            self.es.indices.put_index_template(name=f"{self.index_prefix}-ai", body=ai_template)
            self.es.indices.put_index_template(name=f"{self.index_prefix}-features", body=features_template)
            logger.info("Index templates created successfully")
        except Exception as e:
            logger.warning(f"Failed to create index templates: {e}")

    def export_nids_alert(self, alert: Dict) -> bool:
        """
        Export NIDS signature alert to Elasticsearch

        Args:
            alert: Alert dictionary from NIDS

        Returns:
            True if successful
        """
        try:
            # Add timestamp
            if '@timestamp' not in alert:
                alert['@timestamp'] = alert.get('timestamp', datetime.utcnow().isoformat())

            # Generate index name
            date_suffix = datetime.utcnow().strftime('%Y.%m.%d')
            index_name = f"{self.index_prefix}-nids-alerts-{date_suffix}"

            # Index document
            self.es.index(index=index_name, document=alert)
            self.stats['nids_alerts_sent'] += 1

            return True

        except Exception as e:
            logger.error(f"Failed to export NIDS alert: {e}")
            self.stats['errors'] += 1
            return False

    def export_ai_alert(self, alert: Dict) -> bool:
        """
        Export AI anomaly alert to Elasticsearch

        Args:
            alert: Alert dictionary from AI engine

        Returns:
            True if successful
        """
        try:
            # Add timestamp
            if '@timestamp' not in alert:
                alert['@timestamp'] = alert.get('timestamp', datetime.utcnow().isoformat())

            # Generate index name
            date_suffix = datetime.utcnow().strftime('%Y.%m.%d')
            index_name = f"{self.index_prefix}-ai-alerts-{date_suffix}"

            # Index document
            self.es.index(index=index_name, document=alert)
            self.stats['ai_alerts_sent'] += 1

            return True

        except Exception as e:
            logger.error(f"Failed to export AI alert: {e}")
            self.stats['errors'] += 1
            return False

    def export_network_features(self, features: Dict) -> bool:
        """
        Export network flow features to Elasticsearch

        Args:
            features: Feature dictionary (78 features)

        Returns:
            True if successful
        """
        try:
            # Add timestamp
            if '@timestamp' not in features:
                features['@timestamp'] = datetime.utcnow().isoformat()

            # Calculate derived fields
            features['total_packets'] = features.get('total_fwd_packets', 0) + features.get('total_bwd_packets', 0)
            features['total_bytes'] = features.get('total_fwd_bytes', 0) + features.get('total_bwd_bytes', 0)

            # Generate index name
            date_suffix = datetime.utcnow().strftime('%Y.%m.%d')
            index_name = f"{self.index_prefix}-network-features-{date_suffix}"

            # Index document
            self.es.index(index=index_name, document=features)
            self.stats['features_sent'] += 1

            return True

        except Exception as e:
            logger.error(f"Failed to export features: {e}")
            self.stats['errors'] += 1
            return False

    def bulk_export(self, documents: List[Dict], doc_type: str = 'nids_alert') -> bool:
        """
        Bulk export multiple documents

        Args:
            documents: List of documents to export
            doc_type: Type of document ('nids_alert', 'ai_alert', 'features')

        Returns:
            True if successful
        """
        try:
            date_suffix = datetime.utcnow().strftime('%Y.%m.%d')

            # Determine index name
            if doc_type == 'nids_alert':
                index_name = f"{self.index_prefix}-nids-alerts-{date_suffix}"
            elif doc_type == 'ai_alert':
                index_name = f"{self.index_prefix}-ai-alerts-{date_suffix}"
            else:
                index_name = f"{self.index_prefix}-network-features-{date_suffix}"

            # Prepare bulk actions
            actions = []
            for doc in documents:
                if '@timestamp' not in doc:
                    doc['@timestamp'] = doc.get('timestamp', datetime.utcnow().isoformat())

                actions.append({
                    "_index": index_name,
                    "_source": doc
                })

            # Execute bulk
            success, failed = bulk(self.es, actions, raise_on_error=False)

            logger.info(f"Bulk export: {success} successful, {failed} failed")

            return success > 0

        except Exception as e:
            logger.error(f"Bulk export failed: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get export statistics"""
        return self.stats.copy()

    def print_stats(self):
        """Print statistics"""
        print("\n" + "="*50)
        print("  Elasticsearch Export Statistics")
        print("="*50)
        print(f"NIDS Alerts:    {self.stats['nids_alerts_sent']}")
        print(f"AI Alerts:      {self.stats['ai_alerts_sent']}")
        print(f"Features:       {self.stats['features_sent']}")
        print(f"Errors:         {self.stats['errors']}")
        print("="*50 + "\n")


def main():
    """Test the exporter"""
    print("="*60)
    print("  Elasticsearch Exporter - Test Mode")
    print("="*60)
    print()

    # Initialize exporter
    exporter = ElasticsearchExporter()

    # Connect
    if not exporter.connect():
        logger.error("Failed to connect to Elasticsearch")
        logger.info("Make sure Elasticsearch is running:")
        logger.info("  docker-compose -f elk/docker-compose.yml up -d")
        return 1

    # Create templates
    exporter.create_index_templates()

    # Test NIDS alert
    logger.info("Testing NIDS alert export...")
    nids_alert = {
        "timestamp": datetime.utcnow().isoformat(),
        "severity": "HIGH",
        "severity_level": 3,
        "rule_id": 1002,
        "message": "SQL Injection Attempt",
        "src_ip": "192.168.1.100",
        "dst_ip": "10.0.0.5",
        "src_port": 54321,
        "dst_port": 80,
        "protocol": "TCP"
    }
    exporter.export_nids_alert(nids_alert)

    # Test AI alert
    logger.info("Testing AI alert export...")
    ai_alert = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "ANOMALY",
        "confidence": 0.87,
        "flow_id": 42,
        "details": {
            "ensemble_score": 0.87,
            "inference_time_ms": 3.21,
            "model_predictions": {
                "random_forest": 0.85,
                "isolation_forest": 0.89
            }
        }
    }
    exporter.export_ai_alert(ai_alert)

    # Test features
    logger.info("Testing network features export...")
    features = {
        "duration": 1.523,
        "total_fwd_packets": 10,
        "total_bwd_packets": 8,
        "total_fwd_bytes": 4500,
        "total_bwd_bytes": 3200,
        "flow_bytes_per_sec": 5000.0,
        "syn_flag_count": 1,
        "fin_flag_count": 1
    }
    exporter.export_network_features(features)

    # Show stats
    exporter.print_stats()

    logger.info("✓ Test completed successfully!")
    logger.info("Open Kibana at http://localhost:5601 to view the data")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
