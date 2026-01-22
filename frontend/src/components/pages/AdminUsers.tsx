import React, { useEffect, useState } from "react";
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
} from "@mui/material";
import timetableService from "../../services/timetableService";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "faculty" | "student";
}

const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [search, setSearch] = useState("");

  // ✅ Load users correctly
  const fetchUsers = async () => {
    try {
      const data = await timetableService.listUsers();
      console.log("👥 Users loaded:", data);
      setUsers(data);
    } catch (err) {
      console.error("Failed to load users", err);
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

      <TextField
        label="Search by name or email"
        fullWidth
        sx={{ mb: 2 }}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

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
    </Box>
  );
};

export default AdminUsers;
