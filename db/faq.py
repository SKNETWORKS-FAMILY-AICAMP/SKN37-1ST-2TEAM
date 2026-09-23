from db.connection import fetch_df


# 기업 이름 목록
def get_companies():
    df = fetch_df("""
        SELECT company_name
        FROM company
        ORDER BY company_id
    """)
    return df["company_name"].tolist()


# 기업별 FAQ 카테고리 목록
def get_categories(company):
    df = fetch_df("""
        SELECT DISTINCT fc.category_name
        FROM faq f
        JOIN company c
            ON f.company_id = c.company_id
        JOIN faq_category fc
            ON f.category_id = fc.category_id
        WHERE c.company_name = %s
        ORDER BY fc.category_name
    """, [company])

    return df["category_name"].tolist()


# FAQ 조회
def search_faq(company, category=None, keyword=None):
    sql = """
        SELECT
            f.question,
            f.answer,
            fc.category_name,
            f.source_url,
            f.collected_at
        FROM faq f
        JOIN company c
            ON f.company_id = c.company_id
        JOIN faq_category fc
            ON f.category_id = fc.category_id
        WHERE c.company_name = %s
    """

    params = [company]

    # 카테고리 조건
    if category is not None:
        sql += " AND fc.category_name = %s"
        params.append(category)

    # 검색어 조건
    if keyword is not None and keyword.strip() != "":
        sql += """
            AND (
                f.question LIKE %s
                OR f.answer LIKE %s
            )
        """

        search_keyword = f"%{keyword}%"
        params.extend([search_keyword, search_keyword])

    sql += " ORDER BY f.faq_id DESC"

    return fetch_df(sql, params)