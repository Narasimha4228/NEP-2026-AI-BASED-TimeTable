import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";
// ⚠️ change port/path if your backend is different


export interface Program {
  id: string;
  name: string;
  code: string;
  type: string;
  department: string;
  duration_years: number;
  total_semesters: number;
  credits_required: number;
  description?: string;
  is_active: boolean;
  created_at?: string;
  _id?: string;
  [key: string]: any;
}

export interface Course {
  id: string;
  code: string;
  name: string;
  description?: string;
  credits: number;
  semester: number;
  program_id: string;
  faculty_id?: string;
  hours_per_week: number;
  course_type: string;
  is_active: boolean;
  created_at?: string;
  _id?: string;
  [key: string]: any;
}

export interface StudentGroup {
  id: string;
  name: string;
  course_ids: string[];
  year: number;
  semester: string;
  section: string;
  student_strength: number;
  group_type: string;
  program_id: string;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface Faculty {
  id: string;
  employee_id: string;
  name: string;
  email: string;
  department: string;
  designation: string;
  specialization?: string;
  max_hours_per_week: number;
  is_active: boolean;
  created_at?: string;
  _id?: string;
  [key: string]: any;
}

export interface Room {
  id: string;
  room_number: string;
  building: string;
  floor: number;
  capacity: number;
  room_type: string;
  facilities?: string[];
  is_active: boolean;
  created_at?: string;
  _id?: string;
  [key: string]: any;
}

export interface Timetable {
  id: string;
  title: string;
  program_id: string;
  semester: number;
  academic_year: string;
  status: string;
  entries?: any[];
  created_at?: string;
  updated_at?: string;
  _id?: string;
  [key: string]: any;
}

export interface TimetableCreate {
  title: string;
  program_id: string;
  semester: number;
  academic_year: string;
}

class TimetableService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      "Content-Type": "application/json",
    },
  });

  constructor() {
    // 🔐 Attach JWT token to every request
    this.api.interceptors.request.use((config) => {
      const authStorage = localStorage.getItem("auth-storage");
      console.log("🔐 TimetableService interceptor - authStorage exists:", !!authStorage);
      
      if (authStorage) {
        try {
          const parsed = JSON.parse(authStorage);
          const token = parsed?.state?.token;
          const isAuthenticated = parsed?.state?.isAuthenticated;

          console.log("🔐 TimetableService interceptor - Parsed auth:", {
            hasToken: !!token,
            tokenPreview: token ? `${token.substring(0, 30)}...` : "None",
            isAuthenticated,
          });

          if (token && isAuthenticated) {
            config.headers.Authorization = `Bearer ${token}`;
            console.log("✅ TimetableService - Authorization header added");
          } else {
            console.warn("⚠️ TimetableService - Token missing or not authenticated", {
              token: !!token,
              isAuthenticated,
            });
          }
        } catch (err) {
          console.error("❌ TimetableService - Failed to parse authStorage:", err);
        }
      } else {
        console.warn("⚠️ TimetableService - No auth-storage in localStorage");
      }
      
      return config;
    });

    // Error interceptor for debugging
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error("🚨 TimetableService axios error:", {
          status: error.response?.status,
          statusText: error.response?.statusText,
          message: error.message,
          url: error.config?.url,
        });
        return Promise.reject(error);
      }
    );
  }

  // ===============================
  // USER ACCESS MANAGEMENT (ADMIN)
  // ===============================

  /** Get all users (Admin only) */
  async listUsers(): Promise<any[]> {
    try {
      const response = await this.api.get("/users");

      console.log("📦 Raw users from backend:", response.data);

      const mapped = (response.data || []).map((u: any) => ({
        id: u._id || u.id, // ✅ MongoDB ObjectId mapped correctly
        email: u.email,
        full_name: u.full_name,
        role: u.role,
      }));

      console.log("✅ Mapped users:", mapped);
      return mapped;
    } catch (err: any) {
      console.error("❌ ListUsers error:", {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        message: err.message,
      });
      throw err;
    }
  }

  /** Update user role (Admin only) */
  async updateUserRole(
    userId: string,
    newRole: "admin" | "faculty" | "student"
  ) {
    if (!userId) {
      throw new Error("User ID missing");
    }

    console.log("🔄 Updating role:", userId, newRole);

    const response = await this.api.patch(
      `/users/${userId}/role`, // ✅ FIXED ENDPOINT
      null,
      {
        params: { new_role: newRole },
      }
    );

    console.log("✅ Role updated:", response.data);
    return response.data;
  }

  // ===============================
  // PROGRAMS
  // ===============================

  /**
   * Get programs with optional filters (skip/limit/program_type/department)
   */
  async getPrograms(options?: {
    skip?: number;
    limit?: number;
    program_type?: string;
    department?: string;
  }): Promise<Program[]> {
    const params: any = {};
    if (options?.skip !== undefined) params.skip = options.skip;
    if (options?.limit !== undefined) params.limit = options.limit;
    if (options?.program_type) params.program_type = options.program_type;
    if (options?.department) params.department = options.department;

    const response = await this.api.get('/programs/', { params });
    console.log('📋 Raw programs from backend:', response.data);

    const mapped = (response.data || []).map((p: any) => ({
      id: p.id || p._id || (p._id ? String(p._id) : undefined),
      ...p,
    })) as Program[];

    console.log('✅ Mapped programs:', mapped.length);
    return mapped;
  }

  async createProgram(programData: Partial<Program>) {
    const response = await this.api.post('/programs/', programData);
    console.log('✅ Program created:', response.data);
    return response.data;
  }

  async updateProgram(programId: string, programData: Partial<Program>) {
    if (!programId) throw new Error('Program ID missing');
    const response = await this.api.put(`/programs/${programId}`, programData);
    console.log('✅ Program updated:', response.data);
    return response.data;
  }

  async deleteProgram(programId: string) {
    if (!programId) throw new Error('Program ID missing');
    const response = await this.api.delete(`/programs/${programId}`);
    console.log('✅ Program deleted:', response.data);
    return response.data;
  }

  async getProgramStatistics(programId: string) {
    if (!programId) throw new Error('Program ID missing');
    const response = await this.api.get(`/programs/${programId}/statistics`);
    console.log('📊 Program statistics:', response.data);
    return response.data;
  }

  async getProgramCourses(programId: string, semester?: number) {
    const params: any = {};
    if (semester !== undefined) params.semester = semester;
    const response = await this.api.get(`/programs/${programId}/courses`, { params });
    console.log('📚 Program courses:', response.data);
    return response.data;
  }

  /** Get available years for a program */
  async getAvailableYearsForProgram(programId: string): Promise<number[]> {
    if (!programId) throw new Error('Program ID missing');
    const response = await this.api.get(`/student-groups/program/${programId}/available-years`);
    console.log('📆 Available years for program:', response.data);
    return response.data;
  }

  // ===============================
  // TIMETABLES
  // ===============================

  /** Get all timetables */
  async getAllTimetables(): Promise<Timetable[]> {
    try {
      console.log("📥 Fetching timetables from:", `${this.api.defaults.baseURL}/timetable/`);
      const response = await this.api.get("/timetable/");

      console.log("📦 Raw timetables from backend:", response.data);

      const raw = response.data;

      // If backend returned a single generated timetable object (with `schedule`),
      // normalize to an array containing that single timetable so callers always get an array.
      if (raw && !Array.isArray(raw) && (raw.schedule || raw.timetable || raw.entries)) {
        const single = {
          id: raw.id || raw._id || 'single',
          // keep original keys so frontend can inspect `schedule`/`entries`
          ...raw,
        } as Timetable;
        console.log('ℹ️ Normalized single timetable response to array');
        return [single];
      }

      const mapped = (raw || []).map((t: any) => ({
        id: t.id || t._id || (t._id ? String(t._id) : undefined),
        ...t,
      })) as Timetable[];

      console.log("✅ Mapped timetables:", mapped.length);
      return mapped;
    } catch (error: any) {
      console.error("❌ getAllTimetables error:", {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        request: {
          method: error.config?.method,
          url: error.config?.url,
          headers: error.config?.headers,
        }
      });
      throw error;
    }
  }

  /** Get student's personal timetable */
  async getMyTimetable(): Promise<any> {
    try {
      console.log("📥 Fetching my timetable from:", `${this.api.defaults.baseURL}/timetable/my`);
      const response = await this.api.get("/timetable/my");
      
      console.log("📦 My timetable response:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("❌ getMyTimetable error:", {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
      });
      throw error;
    }
  }

  /** Get available filter options for timetable selection */
  async getFilterOptions(): Promise<any> {
    try {
      console.log("📥 Fetching filter options from:", `${this.api.defaults.baseURL}/timetable/options/filters`);
      const response = await this.api.get("/timetable/options/filters");
      
      console.log("📦 Filter options response:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("❌ getFilterOptions error:", {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
      });
      throw error;
    }
  }

  /** Get a specific timetable by ID with full details including entries */
  async getTimetableById(timetableId: string): Promise<any> {
    try {
      console.log("📥 Fetching timetable by ID from:", `${this.api.defaults.baseURL}/timetable/public/${timetableId}`);
      const response = await this.api.get(`/timetable/public/${timetableId}`);
      
      console.log("📦 Timetable response:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("❌ getTimetableById error:", {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        timetableId,
      });
      throw error;
    }
  }

  /** Filter timetables by department, year, semester, section */
  async filterTimetables(filters: { department_code?: string; program_id?: string; year?: number; semester?: string; section?: string }): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (filters.department_code) params.append('department_code', filters.department_code);
      if (filters.program_id) params.append('program_id', filters.program_id);
      if (filters.year !== undefined && filters.year !== null) params.append('year', String(filters.year));
      if (filters.semester) params.append('semester', filters.semester);
      if (filters.section) params.append('section', filters.section);
      
      const queryString = params.toString();
      const url = `/timetable/filter${queryString ? '?' + queryString : ''}`;
      
      console.log("📥 Fetching filtered timetable from:", `${this.api.defaults.baseURL}${url}`);
      const response = await this.api.get(url);
      
      console.log("📦 Filtered timetable response:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("❌ filterTimetables error:", {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        filters,
      });
      throw error;
    }
  }

  /** Delete timetable */
  async deleteTimetable(timetableId: string) {
    if (!timetableId) throw new Error("Timetable ID missing");

    const response = await this.api.delete(`/timetable/${timetableId}`);
    console.log("🗑️ Timetable deleted:", response.data);
    return response.data;
  }

  /** List all published timetables */
  async listAllTimetables(department_code?: string): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (department_code) params.append('department_code', department_code);
      
      const queryString = params.toString();
      const url = `/timetable/list/all${queryString ? '?' + queryString : ''}`;
      
      console.log("📥 Fetching all timetables from:", `${this.api.defaults.baseURL}${url}`);
      const response = await this.api.get(url);
      
      console.log("📦 All timetables response:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("❌ listAllTimetables error:", {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
      });
      throw error;
    }
  }

  // ===============================
  // COURSES
  // ===============================

  /** Get courses with optional filters */
  async getCourses(programId?: string, semester?: number): Promise<Course[]> {
    const params: any = {};
    if (programId) params.program_id = programId;
    if (semester !== undefined) params.semester = semester;

    const response = await this.api.get('/courses/', { params });
    console.log('📚 Raw courses from backend:', response.data);

    const mapped = (response.data || []).map((c: any) => ({
      id: c.id || c._id || (c._id ? String(c._id) : undefined),
      ...c,
    })) as Course[];

    console.log('✅ Mapped courses:', mapped.length);
    return mapped;
  }

  // ===============================
  // STUDENT GROUPS
  // ===============================

  /** Get student groups (optional program filter) */
  async getStudentGroups(programId?: string): Promise<StudentGroup[]> {
    const params: any = {};
    if (programId) params.program_id = programId;

    const response = await this.api.get('/student-groups/', { params });
    console.log('👥 Raw student groups from backend:', response.data);

    const mapped = (response.data || []).map((g: any) => ({
      id: g.id || g._id || (g._id ? String(g._id) : undefined),
      ...g,
    })) as StudentGroup[];

    console.log('✅ Mapped student groups:', mapped.length);
    return mapped;
  }

  /** Get single student group */
  async getStudentGroup(groupId: string): Promise<StudentGroup> {
    if (!groupId) throw new Error('Group ID missing');
    const response = await this.api.get(`/student-groups/${groupId}`);
    console.log('👥 Raw student group:', response.data);
    const g = { id: response.data.id || response.data._id || String(response.data._id), ...response.data } as StudentGroup;
    return g;
  }

  /** Create student group */
  async createStudentGroup(groupData: Partial<StudentGroup>) {
    const response = await this.api.post('/student-groups/', groupData);
    console.log('✅ Student group created:', response.data);
    return response.data;
  }

  /** Update student group */
  async updateStudentGroup(groupId: string, groupData: Partial<StudentGroup>) {
    if (!groupId) throw new Error('Group ID missing');
    const response = await this.api.put(`/student-groups/${groupId}`, groupData);
    console.log('✅ Student group updated:', response.data);
    return response.data;
  }

  /** Delete student group */
  async deleteStudentGroup(groupId: string) {
    if (!groupId) throw new Error('Group ID missing');
    const response = await this.api.delete(`/student-groups/${groupId}`);
    console.log('✅ Student group deleted:', response.data);
    return response.data;
  }

  /** Create course */
  async createCourse(courseData: Partial<Course>) {
    const response = await this.api.post('/courses/', courseData);
    console.log('✅ Course created:', response.data);
    return response.data;
  }

  /** Update course */
  async updateCourse(courseId: string, courseData: Partial<Course>) {
    if (!courseId) throw new Error('Course ID missing');
    const response = await this.api.put(`/courses/${courseId}`, courseData);
    console.log('✅ Course updated:', response.data);
    return response.data;
  }

  /** Delete course */
  async deleteCourse(courseId: string) {
    if (!courseId) throw new Error('Course ID missing');
    const response = await this.api.delete(`/courses/${courseId}`);
    console.log('✅ Course deleted:', response.data);
    return response.data;
  }

  // ===============================
  // FACULTY
  // ===============================

  /** Get faculty */
  async getFaculty(): Promise<Faculty[]> {
    const response = await this.api.get('/faculty/');
    console.log('👨‍🏫 Raw faculty from backend:', response.data);

    const mapped = (response.data || []).map((f: any) => ({
      id: f.id || f._id || (f._id ? String(f._id) : undefined),
      ...f,
    })) as Faculty[];

    console.log('✅ Mapped faculty:', mapped.length);
    return mapped;
  }

  /** Create faculty */
  async createFaculty(facultyData: Partial<Faculty>) {
    const response = await this.api.post('/faculty/', facultyData);
    console.log('✅ Faculty created:', response.data);
    return response.data;
  }

  /** Update faculty */
  async updateFaculty(facultyId: string, facultyData: Partial<Faculty>) {
    if (!facultyId) throw new Error('Faculty ID missing');
    const response = await this.api.put(`/faculty/${facultyId}`, facultyData);
    console.log('✅ Faculty updated:', response.data);
    return response.data;
  }

  /** Delete faculty */
  async deleteFaculty(facultyId: string) {
    if (!facultyId) throw new Error('Faculty ID missing');
    const response = await this.api.delete(`/faculty/${facultyId}`);
    console.log('✅ Faculty deleted:', response.data);
    return response.data;
  }

  // ===============================
  // ROOMS
  // ===============================

  /** Get rooms with optional filters */
  async getRooms(options?: {
    building?: string;
    room_type?: string;
    min_capacity?: number;
  }): Promise<Room[]> {
    const params: any = {};
    if (options?.building) params.building = options.building;
    if (options?.room_type) params.room_type = options.room_type;
    if (options?.min_capacity !== undefined) params.min_capacity = options.min_capacity;

    const response = await this.api.get('/rooms/', { params });
    console.log('🏢 Raw rooms from backend:', response.data);

    const mapped = (response.data || []).map((r: any) => ({
      id: r.id || r._id || (r._id ? String(r._id) : undefined),
      ...r,
    })) as Room[];

    console.log('✅ Mapped rooms:', mapped.length);
    return mapped;
  }

  /** Create room */
  async createRoom(roomData: Partial<Room>) {
    const response = await this.api.post('/rooms/', roomData);
    console.log('✅ Room created:', response.data);
    return response.data;
  }

  /** Update room */
  async updateRoom(roomId: string, roomData: Partial<Room>) {
    if (!roomId) throw new Error('Room ID missing');
    const response = await this.api.put(`/rooms/${roomId}`, roomData);
    console.log('✅ Room updated:', response.data);
    return response.data;
  }

  /** Delete room */
  async deleteRoom(roomId: string) {
    if (!roomId) throw new Error('Room ID missing');
    const response = await this.api.delete(`/rooms/${roomId}`);
    console.log('✅ Room deleted:', response.data);
    return response.data;
  }

  // ===============================
  // TIMETABLE OPERATIONS
  // ===============================

  /** Get single timetable */
  async getTimetable(timetableId: string): Promise<Timetable> {
    if (!timetableId) throw new Error("Timetable ID missing");

    const response = await this.api.get(`/timetable/${timetableId}`);
    console.log("📋 Raw timetable from backend:", response.data);

    const timetable = {
      id: response.data.id || response.data._id || String(response.data._id),
      ...response.data,
    } as Timetable;

    console.log("✅ Mapped timetable:", timetable);
    return timetable;
  }

  /** Create timetable */
  async createTimetable(timetableData: Partial<Timetable>) {
    const response = await this.api.post('/timetable/', timetableData);
    console.log('✅ Timetable created:', response.data);
    return response.data;
  }

  /** Update timetable */
  async updateTimetable(timetableId: string, timetableData: Partial<Timetable>) {
    if (!timetableId) throw new Error("Timetable ID missing");
    const response = await this.api.put(`/timetable/${timetableId}`, timetableData);
    console.log('✅ Timetable updated:', response.data);
    return response.data;
  }

  /** Generate timetable */
  async generateTimetable(timetableId: string, options?: any) {
    if (!timetableId) throw new Error("Timetable ID missing");
    const response = await this.api.post(`/timetable/${timetableId}/generate`, options || {});
    console.log('✅ Timetable generation started:', response.data);
    return response.data;
  }

  /** Export timetable */
  async exportTimetable(timetableId: string, format: 'excel' | 'pdf' | 'json' | 'csv' = 'excel') {
    if (!timetableId) throw new Error("Timetable ID missing");

    const response = await this.api.get(`/timetable/${timetableId}/export`, {
      params: { format },
      responseType: 'blob',
    });

    console.log('✅ Timetable exported');
    return response.data;
  }

  /** Save draft timetable */
  async saveDraft(draftData: any) {
    const response = await this.api.post('/timetable/draft', draftData);
    console.log('✅ Draft saved:', response.data);
    return response.data;
  }

  /** Get faculty dashboard */
  async getFacultyDashboard(): Promise<any> {
    try {
      const response = await this.api.get('/faculty/dashboard/faculty');
      console.log('👨‍🏫 Faculty dashboard:', response.data);
      return response.data;
    } catch (err) {
      console.error('❌ Error fetching faculty dashboard:', err);
      throw err;
    }
  }
}

export const timetableService = new TimetableService();
export default timetableService;
