"""
Zoho SalesIQ Chatbot Data Extractor for RAG Ingestion

This script extracts conversation flows, intents, responses, and knowledge from
the Acebuddy Zobot export file and transforms it into structured documents
optimized for RAG retrieval with semantic search.

Features:
- Extracts all conversation nodes with context
- Maps user intents to response patterns
- Preserves chatbot personality and response style
- Creates comprehensive Q&A pairs
- Structures knowledge by topic/category
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ZobotDataExtractor:
    """Extract and structure data from Zoho SalesIQ chatbot export"""
    
    def __init__(self, zobot_file_path: str, output_dir: str):
        self.zobot_file_path = Path(zobot_file_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Data structures
        self.action_data = {}
        self.conversation_flows = {}
        self.intent_mappings = {}
        self.response_patterns = defaultdict(list)
        self.knowledge_topics = defaultdict(list)
        
    def load_zobot_data(self) -> Dict:
        """Load the Zobot JSON export file"""
        logger.info(f"Loading Zobot data from: {self.zobot_file_path}")
        
        with open(self.zobot_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Extract action_data (conversation nodes)
        if 'action_data' in data and 'en' in data['action_data']:
            self.action_data = data['action_data']['en']
            logger.info(f"Loaded {len(self.action_data)} conversation nodes")
        
        return data
    
    def extract_intents_from_action(self, action: Dict) -> List[str]:
        """Extract user intents/options from action"""
        intents = []
        
        # From suggestions (button options)
        if 'rendering_config' in action:
            config = action['rendering_config']
            if 'suggestions' in config:
                for suggestion in config['suggestions']:
                    if 'text' in suggestion:
                        intents.append(suggestion['text'])
            
            # From replies with options
            if 'replies' in config:
                for reply in config['replies']:
                    if isinstance(reply, dict) and 'text' in reply:
                        # Check if it's an option/question
                        text = reply['text']
                        if '?' in text or 'select' in text.lower() or 'choose' in text.lower():
                            intents.append(text)
        
        return intents
    
    def extract_responses_from_action(self, action: Dict) -> List[Dict]:
        """Extract bot responses from action"""
        responses = []
        
        if 'rendering_config' not in action:
            return responses
        
        config = action['rendering_config']
        action_name = action.get('name', 'Unknown')
        
        # Text replies
        if 'replies' in config:
            for reply in config['replies']:
                if isinstance(reply, dict) and 'text' in reply:
                    response_data = {
                        'type': 'text',
                        'content': reply['text'],
                        'action_name': action_name,
                        'metadata': {}
                    }
                    
                    # Extract links if present
                    if 'links' in reply:
                        response_data['type'] = 'links'
                        response_data['links'] = reply['links']
                        response_data['metadata']['has_links'] = True
                    
                    # Extract articles if present
                    if 'type' in reply and reply['type'] == 'articles':
                        response_data['type'] = 'articles'
                        if 'articles' in reply:
                            response_data['articles'] = reply['articles']
                        response_data['metadata']['has_articles'] = True
                    
                    responses.append(response_data)
        
        return responses
    
    def build_conversation_flow(self, action_id: str, visited: Set = None) -> Dict:
        """Build a conversation flow starting from an action"""
        if visited is None:
            visited = set()
        
        if action_id in visited or action_id not in self.action_data:
            return None
        
        visited.add(action_id)
        action = self.action_data[action_id]
        
        flow = {
            'action_id': action_id,
            'name': action.get('name', 'Unknown'),
            'type': action.get('type', 1),
            'intents': self.extract_intents_from_action(action),
            'responses': self.extract_responses_from_action(action),
            'next_actions': []
        }
        
        # Follow next actions
        if 'criteria' in action:
            criteria = action['criteria']
            
            # Default next action
            if 'default' in criteria and 'next_action_id' in criteria['default']:
                next_id = criteria['default']['next_action_id']
                if next_id not in visited:
                    next_flow = self.build_conversation_flow(str(next_id), visited.copy())
                    if next_flow:
                        flow['next_actions'].append(next_flow)
            
            # Rule-based next actions
            if 'rules' in criteria:
                for rule in criteria['rules']:
                    if 'next_action_id' in rule:
                        next_id = rule['next_action_id']
                        if next_id not in visited:
                            next_flow = self.build_conversation_flow(str(next_id), visited.copy())
                            if next_flow:
                                flow['next_actions'].append(next_flow)
        
        return flow
    
    def extract_topic_from_name(self, name: str) -> str:
        """Extract topic category from action name"""
        name_lower = name.lower()
        
        # Define topic mappings
        topic_keywords = {
            'password': 'Password Reset',
            'user': 'User Management',
            'application': 'Application Management',
            'quickbooks': 'QuickBooks',
            'qb': 'QuickBooks',
            'office': 'Office 365',
            'rdp': 'Server Access',
            'server': 'Server Management',
            'disk': 'Disk Space',
            'memory': 'Memory/RAM',
            'ram': 'Memory/RAM',
            'printer': 'Printer Setup',
            'scanner': 'Scanner Setup',
            'uniprint': 'Printer Setup',
            'tsscan': 'Scanner Setup',
            'proseries': 'ProSeries',
            'lacerte': 'Lacerte',
            'drake': 'Drake Tax',
            'sage': 'Sage',
            'atx': 'ATX',
            'upgrade': 'Application Upgrades',
            'installation': 'Application Installation',
            'forward': 'Support Escalation',
            'busy': 'Support Escalation'
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in name_lower:
                return topic
        
        return 'General Support'
    
    def create_qa_document(self, intent: str, responses: List[Dict], topic: str, context: str = '') -> Dict:
        """Create a Q&A document for RAG"""
        # Combine all text responses
        answer_parts = []
        links = []
        articles = []
        
        for resp in responses:
            if resp['type'] == 'text':
                answer_parts.append(resp['content'])
            elif resp['type'] == 'links':
                answer_parts.append(resp['content'])
                if 'links' in resp:
                    links.extend(resp['links'])
            elif resp['type'] == 'articles':
                answer_parts.append(resp['content'])
                if 'articles' in resp:
                    articles.extend(resp['articles'])
        
        full_answer = '\n\n'.join(answer_parts)
        
        # Create document
        doc = {
            'question': intent,
            'answer': full_answer,
            'topic': topic,
            'metadata': {
                'source': 'Acebuddy Chatbot',
                'has_links': len(links) > 0,
                'has_articles': len(articles) > 0,
                'context': context
            }
        }
        
        if links:
            doc['links'] = links
        if articles:
            doc['articles'] = articles
        
        return doc
    
    def extract_all_qa_pairs(self) -> List[Dict]:
        """Extract all Q&A pairs from the chatbot"""
        qa_documents = []
        
        logger.info("Extracting Q&A pairs from conversation flows...")
        
        for action_id, action in self.action_data.items():
            # Extract intents and responses
            intents = self.extract_intents_from_action(action)
            responses = self.extract_responses_from_action(action)
            
            if not responses:
                continue
            
            # Determine topic
            topic = self.extract_topic_from_name(action.get('name', ''))
            
            # If there are specific intents (user options), create individual Q&A pairs
            if intents:
                for intent in intents:
                    doc = self.create_qa_document(
                        intent=intent,
                        responses=responses,
                        topic=topic,
                        context=action.get('name', '')
                    )
                    qa_documents.append(doc)
            else:
                # Create a general Q&A based on the action name
                action_name = action.get('name', '').replace('Card', '').replace('Quick reply', '').strip()
                if action_name and action_name not in ['Go to', 'Associate tags', 'Send Message']:
                    doc = self.create_qa_document(
                        intent=f"How do I {action_name.lower()}?",
                        responses=responses,
                        topic=topic,
                        context=action_name
                    )
                    qa_documents.append(doc)
        
        logger.info(f"Extracted {len(qa_documents)} Q&A pairs")
        return qa_documents
    
    def create_topic_document(self, topic: str, qa_pairs: List[Dict]) -> str:
        """Create a comprehensive topic document"""
        doc_lines = [
            f"# {topic}",
            "",
            f"This document contains comprehensive support information about {topic} from the AceBuddy support system.",
            "",
            "---",
            ""
        ]
        
        for i, qa in enumerate(qa_pairs, 1):
            doc_lines.extend([
                f"## Question {i}: {qa['question']}",
                "",
                "**Answer:**",
                "",
                qa['answer'],
                ""
            ])
            
            # Add links if present
            if 'links' in qa and qa['links']:
                doc_lines.append("**Related Links:**")
                doc_lines.append("")
                for link in qa['links']:
                    doc_lines.append(f"- [{link.get('text', 'Link')}]({link.get('url', '')})")
                doc_lines.append("")
            
            doc_lines.append("---")
            doc_lines.append("")
        
        return '\n'.join(doc_lines)
    
    def save_documents(self, qa_documents: List[Dict]):
        """Save extracted documents in multiple formats"""
        logger.info("Saving documents...")
        
        # 1. Save all Q&A pairs as JSON
        json_output = self.output_dir / 'zobot_qa_pairs.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(qa_documents, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON: {json_output}")
        
        # 2. Group by topic and create markdown documents
        topic_groups = defaultdict(list)
        for doc in qa_documents:
            topic_groups[doc['topic']].append(doc)
        
        topic_dir = self.output_dir / 'topics'
        topic_dir.mkdir(exist_ok=True)
        
        for topic, qa_pairs in topic_groups.items():
            # Create safe filename
            safe_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
            topic_file = topic_dir / f'{safe_topic}.md'
            
            # Create topic document
            topic_doc = self.create_topic_document(topic, qa_pairs)
            
            with open(topic_file, 'w', encoding='utf-8') as f:
                f.write(topic_doc)
            
            logger.info(f"Saved topic document: {topic_file} ({len(qa_pairs)} Q&A pairs)")
        
        # 3. Create a master document with all information
        master_doc = self.create_master_document(topic_groups)
        master_file = self.output_dir / 'acebuddy_chatbot_knowledge.md'
        with open(master_file, 'w', encoding='utf-8') as f:
            f.write(master_doc)
        logger.info(f"Saved master document: {master_file}")
        
        # 4. Create a summary report
        self.create_summary_report(qa_documents, topic_groups)
    
    def create_master_document(self, topic_groups: Dict[str, List[Dict]]) -> str:
        """Create a comprehensive master knowledge document"""
        lines = [
            "# AceBuddy Support Chatbot - Complete Knowledge Base",
            "",
            "This document contains all support knowledge extracted from the AceBuddy Zoho SalesIQ chatbot.",
            "It includes conversation flows, Q&A pairs, procedures, and support responses.",
            "",
            "**Source:** Acebuddy Zobot Export",
            f"**Total Topics:** {len(topic_groups)}",
            f"**Total Q&A Pairs:** {sum(len(pairs) for pairs in topic_groups.values())}",
            "",
            "---",
            "",
            "# Table of Contents",
            ""
        ]
        
        # Add TOC
        for i, topic in enumerate(sorted(topic_groups.keys()), 1):
            lines.append(f"{i}. [{topic}](#{topic.lower().replace(' ', '-').replace('/', '')})")
        
        lines.extend(["", "---", ""])
        
        # Add all topics
        for topic in sorted(topic_groups.keys()):
            qa_pairs = topic_groups[topic]
            lines.append(f"\n\n# {topic}")
            lines.append("")
            lines.append(f"**Number of Q&A Pairs:** {len(qa_pairs)}")
            lines.append("")
            lines.append("---")
            lines.append("")
            
            for i, qa in enumerate(qa_pairs, 1):
                lines.extend([
                    f"## {topic} - Q{i}",
                    "",
                    f"**Question:** {qa['question']}",
                    "",
                    "**Answer:**",
                    "",
                    qa['answer'],
                    ""
                ])
                
                if 'links' in qa and qa['links']:
                    lines.append("**Resources:**")
                    lines.append("")
                    for link in qa['links']:
                        lines.append(f"- [{link.get('text', 'Resource')}]({link.get('url', '')})")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
        
        return '\n'.join(lines)
    
    def create_summary_report(self, qa_documents: List[Dict], topic_groups: Dict[str, List[Dict]]):
        """Create extraction summary report"""
        report_lines = [
            "# Zobot Data Extraction Summary",
            "",
            f"**Extraction Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Source File:** {self.zobot_file_path.name}",
            "",
            "## Statistics",
            "",
            f"- **Total Conversation Nodes:** {len(self.action_data)}",
            f"- **Total Q&A Pairs Extracted:** {len(qa_documents)}",
            f"- **Topics Identified:** {len(topic_groups)}",
            "",
            "## Topics Breakdown",
            ""
        ]
        
        # Sort topics by number of Q&A pairs
        sorted_topics = sorted(topic_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for topic, qa_pairs in sorted_topics:
            report_lines.append(f"- **{topic}:** {len(qa_pairs)} Q&A pairs")
        
        report_lines.extend([
            "",
            "## Sample Questions by Topic",
            ""
        ])
        
        for topic, qa_pairs in sorted_topics:
            if qa_pairs:
                report_lines.append(f"### {topic}")
                report_lines.append("")
                # Show first 3 questions
                for qa in qa_pairs[:3]:
                    report_lines.append(f"- {qa['question']}")
                report_lines.append("")
        
        report_lines.extend([
            "",
            "## Output Files Generated",
            "",
            f"1. **JSON Database:** `zobot_qa_pairs.json` - {len(qa_documents)} Q&A pairs",
            f"2. **Topic Documents:** `topics/` folder - {len(topic_groups)} markdown files",
            "3. **Master Document:** `acebuddy_chatbot_knowledge.md` - Complete knowledge base",
            "4. **This Report:** `extraction_summary.md`",
            "",
            "## Next Steps",
            "",
            "1. Review the extracted documents in the `topics/` folder",
            "2. Check the master document for completeness",
            "3. Run the RAG ingestion script to add this data to ChromaDB:",
            "   ```bash",
            "   python scripts/ingest_zobot_to_rag.py",
            "   ```",
            ""
        ])
        
        summary_file = self.output_dir / 'extraction_summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Saved summary report: {summary_file}")
    
    def run(self):
        """Main extraction workflow"""
        logger.info("=" * 60)
        logger.info("Zobot Data Extraction Started")
        logger.info("=" * 60)
        
        try:
            # Load data
            zobot_data = self.load_zobot_data()
            
            # Extract Q&A pairs
            qa_documents = self.extract_all_qa_pairs()
            
            # Save all documents
            self.save_documents(qa_documents)
            
            logger.info("=" * 60)
            logger.info("Extraction Complete!")
            logger.info(f"Output directory: {self.output_dir}")
            logger.info(f"Total Q&A pairs extracted: {len(qa_documents)}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            return False


def main():
    """Main execution"""
    import os
    
    # Define paths
    workspace_root = Path(__file__).parent.parent
    zobot_file = workspace_root / 'Ticket Data' / 'Acebuddy'
    output_dir = workspace_root / 'data' / 'zobot_extracted'
    
    # Check if file exists
    if not zobot_file.exists():
        logger.error(f"Zobot file not found: {zobot_file}")
        return False
    
    # Run extraction
    extractor = ZobotDataExtractor(
        zobot_file_path=str(zobot_file),
        output_dir=str(output_dir)
    )
    
    success = extractor.run()
    
    if success:
        logger.info("\n🎉 Success! Zobot data extracted and ready for RAG ingestion.")
        logger.info(f"\n📁 Check the output in: {output_dir}")
        logger.info("\n📝 Review the extraction_summary.md for details.")
        logger.info("\n🚀 Next: Run 'python scripts/ingest_zobot_to_rag.py' to add to ChromaDB")
    
    return success


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
