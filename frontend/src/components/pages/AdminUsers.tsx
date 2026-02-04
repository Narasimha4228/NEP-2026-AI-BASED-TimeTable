import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  TextField,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Alert,
} from "@mui/material";
import timetableService from "../../services/timetableService";
import { useAuthStore } from "../../store/authStore";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "faculty" | "student";
}

const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();
  const { logout } = useAuthStore();

  // ✅ Load users correctly
  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log("📥 Fetching users...");
      const data = await timetableService.listUsers();
      console.log("👥 Users loaded:", data);
      setUsers(data);
      if (data.length === 0) {
        setError("No users found");
      }
    } catch (err: any) {
      console.error("❌ Failed to load users:", err);
      
      // Check if it's a 401 Unauthorized error
      if (err.response?.status === 401) {
        console.error("🔑 Token expired or invalid, logging out...");
        logout();
        navigate("/login");
        return;
      }
      
      const errorMsg = err.response?.data?.detail || err.response?.statusText || err.message || "Unknown error";
      const fullError = `Failed to load users: ${errorMsg} (${err.response?.status || "Network Error"})`;
      console.error("📋 Full error:", fullError);
      setError(fullError);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // ✅ Role update (FIXED)
  const handleRoleChange = async (
    userId: string,
    newRole: "admin" | "faculty" | "student"
  ) => {
    console.log("🆔 userId:", userId);

    if (!userId) {
      alert("User ID missing");
      return;
    }

    try {
      await timetableService.updateUserRole(userId, newRole);
      alert("Role updated successfully");
      fetchUsers(); // refresh table
    } catch (error) {
      console.error("Role update failed", error);
      alert("Failed to update role");
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.full_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Access Management
      </Typography>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading users...</Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && (
        <>
          <TextField
            label="Search by name or email"
            fullWidth
            sx={{ mb: 2 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          {users.length === 0 ? (
            <Alert severity="info">No users available</Alert>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Action</TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>

                    <TableCell>
                      <Select
                        value={user.role}
                        size="small"
                        onChange={(e) =>
                          handleRoleChange(
                            user.id,
                            e.target.value as "admin" | "faculty" | "student"
                          )
                        }
                      >
                        <MenuItem value="student">Student</MenuItem>
                        <MenuItem value="faculty">Faculty</MenuItem>
                        <MenuItem value="admin">Admin</MenuItem>
                      </Select>
                    </TableCell>

                    <TableCell>
                      <Button size="small" variant="outlined">
                        Update
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </>
      )}
    </Box>
  );
};

export default AdminUsers;
