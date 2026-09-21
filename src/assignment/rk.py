

from pymongo import MongoClient, errors


class AttendanceManager:

    def __init__(self, mongo_url, db_name="college_attendance"):
        self.client = None
        self.database = None
        self.student_collection = None
        self.attendance_collection = None

        try:
            self.client = MongoClient(
                mongo_url,
                serverSelectionTimeoutMS=5000
            )

            self.client.admin.command("ping")

            self.database = self.client[db_name]
            self.student_collection = self.database.students
            self.attendance_collection = self.database.attendance

          
            self.student_collection.create_index(
                "roll_no",
                unique=True
            )

            print(f"[INFO] Connected to MongoDB database: {db_name}")

        except errors.PyMongoError as error:
            print(f"[ERROR] MongoDB connection failed: {error}")
            raise

    def add_student(self, name, roll_no, email, course):

        values = [name, roll_no, email, course]

        if any(not str(value).strip() for value in values):
            print("[ERROR] Please provide all student details.")
            return False

        roll_no = str(roll_no).strip()

        try:

            if self.student_collection.count_documents(
                {"roll_no": roll_no},
                limit=1
            ):
                print(f"[WARNING] Roll number {roll_no} already exists.")
                return False

            student = {
                "name": name.strip(),
                "roll_no": roll_no,
                "email": email.strip(),
                "course": course.strip()
            }

            result = self.student_collection.insert_one(student)

            print(
                f"[SUCCESS] Student added successfully. "
                f"ID: {result.inserted_id}"
            )

            return True

        except errors.DuplicateKeyError:
            print("[ERROR] Roll number must be unique.")
            return False

        except errors.PyMongoError as error:
            print(f"[ERROR] Unable to add student: {error}")
            return False

    def mark_attendance(self, roll_no, date, status):

        roll_no = str(roll_no).strip()
        status = str(status).strip().title()

        if status not in ("Present", "Absent"):
            print(
                "[ERROR] Status must be either "
                "'Present' or 'Absent'."
            )
            return False

        try:

            student = self.student_collection.find_one(
                {"roll_no": roll_no}
            )

            if student is None:
                print(
                    f"[ERROR] No student found with roll number "
                    f"{roll_no}."
                )
                return False

            attendance = {
                "roll_no": roll_no,
                "student_name": student["name"],
                "date": str(date).strip(),
                "status": status
            }

            result = self.attendance_collection.insert_one(
                attendance
            )

            print(
                f"[SUCCESS] Attendance marked for "
                f"{student['name']} - {status}"
            )

            return str(result.inserted_id)

        except errors.PyMongoError as error:
            print(
                f"[ERROR] Could not save attendance: {error}"
            )
            return False

  
    def display_attendance(self):

        try:
            records = self.attendance_collection.find(
                {},
                {
                    "_id": 1,
                    "roll_no": 1,
                    "student_name": 1,
                    "date": 1,
                    "status": 1
                }
            )

            records = list(records)

            if not records:
                print("\nNo attendance records available.")
                return []

            print("\n" + "=" * 90)
            print("                    ATTENDANCE RECORDS")
            print("=" * 90)

            print(
                f"{'ID':<24}"
                f"{'ROLL NO':<15}"
                f"{'NAME':<20}"
                f"{'DATE':<15}"
                f"STATUS"
            )

            print("-" * 90)

            result = []

            for item in records:

                record = {
                    "id": str(item["_id"]),
                    "roll_no": item.get("roll_no"),
                    "student_name": item.get("student_name"),
                    "date": item.get("date"),
                    "status": item.get("status")
                }

                result.append(record)

                print(
                    f"{record['id']:<24}"
                    f"{record['roll_no']:<15}"
                    f"{record['student_name']:<20}"
                    f"{record['date']:<15}"
                    f"{record['status']}"
                )

            print("=" * 90)

            return result

        except errors.PyMongoError as error:
            print(
                f"[ERROR] Unable to retrieve attendance: {error}"
            )
            return []


    def remove_student(self, roll_no):

        roll_no = str(roll_no).strip()

        try:

            student = self.student_collection.find_one(
                {"roll_no": roll_no}
            )

            if student is None:
                print(
                    f"[WARNING] Student {roll_no} does not exist."
                )
                return False

            deleted = self.student_collection.delete_one(
                {"roll_no": roll_no}
            )

            if deleted.deleted_count == 1:
                print(
                    f"[SUCCESS] Student "
                    f"{student['name']} deleted."
                )
                return True

            return False

        except errors.PyMongoError as error:
            print(
                f"[ERROR] Error while deleting student: {error}"
            )
            return False

   
    def close(self):

        if self.client:
            self.client.close()
            print("[INFO] MongoDB connection closed.")