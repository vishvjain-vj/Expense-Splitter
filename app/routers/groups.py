from fastapi import APIRouter, HTTPException
from app.schemas.schemas import GroupCreate, GroupResponse
from app.models.database import get_connection

router = APIRouter()


@router.post("/", response_model=GroupResponse, status_code=201)
def create_group(body: GroupCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO groups_tbl (name, description) VALUES (%s, %s)",
            (body.name, body.description)
        )
        conn.commit()
        group_id = cursor.lastrowid
        cursor.execute("SELECT * FROM groups_tbl WHERE id = %s", (group_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


@router.get("/", response_model=list[GroupResponse])
def list_groups():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM groups_tbl ORDER BY created_at DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM groups_tbl WHERE id = %s", (group_id,))
        group = cursor.fetchone()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group
    finally:
        cursor.close()
        conn.close()


@router.delete("/{group_id}", status_code=204)
def delete_group(group_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM groups_tbl WHERE id = %s", (group_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Group not found")
    finally:
        cursor.close()
        conn.close()
