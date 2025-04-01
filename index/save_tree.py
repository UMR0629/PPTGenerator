import sqlite3
from typing import List, Dict, Any
import json
from index import PaperInfo, Node, SectionContent, PaperSectionSummary


class PaperInfoDB:
    def __init__(self, db_path: str = "paper_info.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Paper metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    date TEXT NOT NULL,
                    journal TEXT NOT NULL,
                    ppt_presenter TEXT NOT NULL,
                    ppt_date TEXT NOT NULL,
                    image_list TEXT NOT NULL
                )
            """)

            # Outline nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outline_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    parent_name TEXT,
                    text_content TEXT,
                    key_points TEXT,
                    tables TEXT,
                    figures TEXT,
                    FOREIGN KEY (paper_id) REFERENCES papers(id)
                )
            """)

            conn.commit()

    def save_paper(self, paper: PaperInfo) -> int:
        """Save PaperInfo object to database and return paper_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Save paper metadata
            cursor.execute("""
                INSERT INTO papers (
                    title, authors, date, journal, ppt_presenter, ppt_date, image_list
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                paper.title,
                json.dumps(paper.authors),
                paper.date,
                paper.journal,
                paper.ppt_presenter,
                paper.ppt_date,
                json.dumps(paper.image_list)
            ))
            paper_id = cursor.lastrowid

            # Save outline structure using recursive approach
            self._save_node_recursive(cursor, paper_id, paper.outline_root)

            conn.commit()
            return paper_id

    def _save_node_recursive(self, cursor, paper_id: int, node: Node, parent_name: str = None):
        """Recursively save outline nodes"""
        # Prepare content data
        text_content = node.content.text if node.content else None
        key_points = json.dumps(node.content.summary.key_points) if node.content and node.content.summary else None
        tables = json.dumps(node.content.summary.tables) if node.content and node.content.summary else None
        figures = json.dumps(node.content.summary.figures) if node.content and node.content.summary else None

        # Insert current node
        cursor.execute("""
            INSERT INTO outline_nodes (
                paper_id, title, parent_name, text_content, key_points, tables, figures
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_id,
            node.name,
            parent_name,
            text_content,
            key_points,
            tables,
            figures
        ))
        current_id = cursor.lastrowid

        # Save children recursively
        for child in node.children:
            self._save_node_recursive(cursor, paper_id, child, node.name)

    def load_paper(self, paper_id: int) -> PaperInfo:
        """Load PaperInfo object from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Load paper metadata
            cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
            paper_data = cursor.fetchone()
            if not paper_data:
                raise ValueError(f"Paper with id {paper_id} not found")

            # Reconstruct PaperInfo object
            paper = PaperInfo(
                title=paper_data[1],
                authors=json.loads(paper_data[2]),
                date=paper_data[3],
                journal=paper_data[4],
                ppt_presenter=paper_data[5],
                ppt_date=paper_data[6]
            )
            paper.image_list = json.loads(paper_data[7])

            # Load outline structure
            cursor.execute("""
                SELECT * FROM outline_nodes 
                WHERE paper_id = ?
                ORDER BY id
            """, (paper_id,))
            nodes_data = cursor.fetchall()

            if nodes_data:
                # First pass: create all nodes without hierarchy
                nodes_map = {}
                for node_data in nodes_data:
                    node_id = node_data[0]
                    parent_name = node_data[3]

                    # Create SectionContent if content exists
                    content = None
                    if node_data[4] is not None:  # text_content exists
                        summary_data = {
                            "key_points": json.loads(node_data[5]) if node_data[5] else [],
                            "tables": json.loads(node_data[6]) if node_data[6] else [],
                            "figures": json.loads(node_data[7]) if node_data[7] else []
                        }
                        summary = PaperSectionSummary(**summary_data)
                        content = SectionContent(
                            text=node_data[4],
                            summary=summary
                        )
                    parent_node = paper.find_outline_section(parent_name) if parent_name else None
                    node = Node(
                        name=node_data[2],
                        parent=parent_node,
                        content=content
                    )
                    nodes_map[node_id] = (node, parent_name)  # Store node and its parent_id

                # # Second pass: build hierarchy
                # root_node = None
                # for node_id, (node, parent_id) in nodes_map.items():
                #     if parent_id is None:
                #         root_node = node
                #         paper.outline_root = node
                #     else:
                #         parent_node = nodes_map[parent_id][0]  # Get the Node object
                #         parent_node.children.append(node)
                #         node.parent = parent_node
                #
                # if not root_node:
                #     raise ValueError("No root node found in the outline structure")

            return paper

    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Get list of all papers with basic info"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, authors, date FROM papers")
            papers = []
            for row in cursor.fetchall():
                papers.append({
                    "id": row[0],
                    "title": row[1],
                    "authors": json.loads(row[2]),
                    "date": row[3]
                })
            return papers