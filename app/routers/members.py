from fastapi import APIRouter, HTTPException
from app.schemas.schemas import MemberCreate, MemberResponse
from app.models.database import get_connection

router = APIRouter()


@router.post("/{group_id}/members", response_model=MemberResponse, status_code=201)
def add_member(group_id: int, body: MemberCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify group exists
        cursor.execute("SELECT id FROM groups_tbl WHERE id = %s", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Group not found")

        cursor.execute(
            "INSERT INTO members (group_id, name, email) VALUES (%s, %s, %s)",
            (group_id, body.name, body.email)
        )
        conn.commit()
        member_id = cursor.lastrowid
        cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
        return cursor.fetchone()

    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail="Member with this email already exists in group")
        raise
    finally:
        cursor.close()
        conn.close()


@router.get("/{group_id}/members", response_model=list[MemberResponse])
def list_members(group_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM members WHERE group_id = %s", (group_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


@router.delete("/{group_id}/members/{member_id}", status_code=204)
def remove_member(group_id: int, member_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM members WHERE id = %s AND group_id = %s",
            (member_id, group_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Member not found in this group")
    finally:
        cursor.close()
        conn.close()
