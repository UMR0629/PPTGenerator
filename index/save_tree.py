import sqlite3
from typing import List, Dict, Any
import json

#from index.testmain import summary
from index_module import PaperInfo, Node, SectionContent, PaperSectionSummary, TableorFigure


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
                    summary_id INTEGER,
                    key_points TEXT,
                    tables TEXT,
                    figures TEXT,
                    FOREIGN KEY (paper_id) REFERENCES papers(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tables_figures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    summary_id INTEGER,
                    item_type TEXT,
                    number TEXT,
                    enable INTEGER,
                    path TEXT,
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
        # 如果
        if node.content is not None:
            if len(node.content.summary) != 0:
                #print(text_content)
                summary_id = 0
                for summary_content in node.content.summary:
                    summary_id += 1
                    key_points = json.dumps(summary_content.key_points) if node.content and node.content.summary else None
                    tables = node.content.summary.tables
                    figures = node.content.summary.figures
                    if len(tables) != 0:
                        for table in tables:
                            cursor.execute("""
                                INSERT INTO tables_figures (
                                    paper_id, title, summary_id, item_type, number, enable, path
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                paper_id,
                                node.name,
                                summary_id,
                                "TABLE",
                                table.number,
                                table.enable,
                                table.path
                            ))
                    if len(figures) != 0:
                        for figure in figures:
                            cursor.execute("""
                                INSERT INTO tables_figures (
                                    paper_id, title, summary_id, item_type, number, enable, path
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                paper_id,
                                node.name,
                                summary_id,
                                "FIGURE",
                                figure.number,
                                figure.enable,
                                figure.path
                            ))
                    #tables = json.dumps(summary_content.tables) if node.content and node.content.summary else None
                    #figures = json.dumps(summary_content.figures) if node.content and node.content.summary else None
                    tables = None
                    figures = None

                    # Insert current node
                    cursor.execute("""
                        INSERT INTO outline_nodes (
                            paper_id, title, parent_name, text_content, summary_id, key_points, tables, figures
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        paper_id,
                        node.name,
                        parent_name,
                        text_content,
                        summary_id,
                        key_points,
                        tables,
                        figures
                    ))
                    current_id = cursor.lastrowid
            else:
                #print(text_content)
                summary_id = None
                key_points = None
                tables = None
                figures = None

                # Insert current node
                cursor.execute("""
                        INSERT INTO outline_nodes (
                            paper_id, title, parent_name, text_content, summary_id, key_points, tables, figures
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                    paper_id,
                    node.name,
                    parent_name,
                    text_content,
                    summary_id,
                    key_points,
                    tables,
                    figures
                ))
                current_id = cursor.lastrowid

        else:
            summary_id = None
            key_points =  None
            tables =  None
            figures =  None
            text_content = None

            # Insert current node
            cursor.execute("""
                INSERT INTO outline_nodes (
                    paper_id, title, parent_name, text_content, summary_id, key_points, tables, figures
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper_id,
                node.name,
                parent_name,
                text_content,
                summary_id,
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
                    # 如果是已经插入树的结点
                    if paper.find_outline_section(node_data[2]) is not None:
                        node_find = paper.find_outline_section(node_data[2])

                        # 如果database存在content（section）内容
                        if node_data[4] is not None:
                            # 如果树中的node没有content叶子，则创建
                            if node_find.content is None:
                                paper.add_content_to_leaf(node_data[2], nodes_data[4])
                            # 如果database存在keypoints，说明有summary
                            if node_data[6] is not None:
                                key_points = json.loads(node_data[6]) if node_data[6] else []
                                summary = PaperSectionSummary(key_points)
                                # 查询该论文、该section、该summery下的table数据
                                cursor.execute("""
                                    SELECT * FROM outline_nodes 
                                    WHERE paper_id = ? and title = ? and summary_id = ? and item_type = ?
                                    ORDER BY id
                                """, (paper_id, node_data[2], node_data[5], "TABLE",))
                                tables_data = cursor.fetchall()
                                for table_data in tables_data:
                                    new_table = TableorFigure(table_data[5], table_data[6], table_data[7])
                                    summary.tables.append(new_table)
                                # 查询该论文、该section、该summery下的figure数据
                                cursor.execute("""
                                    SELECT * FROM outline_nodes 
                                    WHERE paper_id = ? and title = ? and summary_id = ? and item_type = ?
                                    ORDER BY id
                                """, (paper_id, node_data[2], node_data[5], "FIGURE",))
                                figures_data = cursor.fetchall()
                                for figure_data in figures_data:
                                    new_figure = TableorFigure(figure_data[5], figure_data[6], figure_data[7])
                                    summary.tables.append(new_figure)
                                node_find.content.add_summary(summary)

                    # 如果是新的结点
                    else:
                        content = None
                        # 如果存在content（section）内容
                        if node_data[4] is not None:
                            content = SectionContent(node_data[4])
                            if node_data[6] is not None:
                                key_points = json.loads(node_data[6]) if node_data[6] else []
                                summary = PaperSectionSummary(key_points)
                                # 查询该论文、该section、该summery下的table数据
                                cursor.execute("""
                                    SELECT * FROM outline_nodes 
                                    WHERE paper_id = ? and title = ? and summary_id = ? and item_type = ?
                                    ORDER BY id
                                """, (paper_id, node_data[2], node_data[5], "TABLE",))
                                tables_data = cursor.fetchall()
                                for table_data in tables_data:
                                    new_table = TableorFigure(table_data[5], table_data[6], table_data[7])
                                    summary.tables.append(new_table)
                                # 查询该论文、该section、该summery下的figure数据
                                cursor.execute("""
                                    SELECT * FROM outline_nodes 
                                    WHERE paper_id = ? and title = ? and summary_id = ? and item_type = ?
                                    ORDER BY id
                                """, (paper_id, node_data[2], node_data[5], "FIGURE",))
                                figures_data = cursor.fetchall()
                                for figure_data in figures_data:
                                    new_figure = TableorFigure(figure_data[5], figure_data[6], figure_data[7])
                                    summary.tables.append(new_figure)
                                content.add_summary(summary)
                        parent_node = paper.find_outline_section(parent_name) if parent_name else None
                        node = Node(
                            name=node_data[2],
                            parent=parent_node,
                            content=content
                        )
                        nodes_map[node_id] = (node, parent_name)  # Store node and its parent_id


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