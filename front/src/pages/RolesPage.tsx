import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { rolesService } from '../api/services';
import { RoleResponse, UpdateRoleRequest, UserRoleAssignment } from '../types';

export function RolesPage() {
  const queryClient = useQueryClient();
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [newRole, setNewRole] = useState({ name: '', description: '' });
  const [error, setError] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<RoleResponse | null>(null);
  const [userIds, setUserIds] = useState('');

  // Получение списка ролей
  const { data: rolesData, isLoading } = useQuery({
    queryKey: ['roles', currentPage, pageSize],
    queryFn: () => rolesService.getRoles(currentPage, pageSize),
    select: (response) => response.data,
  });

  // Получение пользователей роли
  const { data: roleUsers } = useQuery({
    queryKey: ['roleUsers', selectedRole?.id],
    queryFn: () => selectedRole ? rolesService.getUsersByRole(selectedRole.id) : null,
    enabled: !!selectedRole,
  });

  // Создание роли
  const createRoleMutation = useMutation({
    mutationFn: (data: UpdateRoleRequest) => rolesService.createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      setNewRole({ name: '', description: '' });
      setError(null);
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Failed to create role');
    },
  });

  // Удаление роли
  const deleteRoleMutation = useMutation({
    mutationFn: (roleId: string) => rolesService.deleteRole(roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  });

  // Назначение пользователей на роль
  const assignUsersMutation = useMutation({
    mutationFn: ({ roleId, userIds }: { roleId: string; userIds: string[] }) =>
      rolesService.assignUsersToRole(roleId, { user_ids: userIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roleUsers'] });
      setUserIds('');
    },
  });

  // Удаление пользователей из роли
  const removeUsersMutation = useMutation({
    mutationFn: ({ roleId, userIds }: { roleId: string; userIds: string[] }) =>
      rolesService.removeUsersFromRole(roleId, { user_ids: userIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roleUsers'] });
    },
  });

  const handleCreateRole = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRole.name) return;
    createRoleMutation.mutate(newRole);
  };

  const handleDeleteRole = (roleId: string) => {
    if (window.confirm('Are you sure you want to delete this role?')) {
      deleteRoleMutation.mutate(roleId);
    }
  };

  const handleAssignUsers = (roleId: string) => {
    const userIdList = userIds.split(',').map(id => id.trim());
    assignUsersMutation.mutate({ roleId, userIds: userIdList });
  };

  const handleRemoveUser = (roleId: string, userId: string) => {
    removeUsersMutation.mutate({ roleId, userIds: [userId] });
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="container mx-auto py-8">
      <Card>
        <CardHeader>
          <CardTitle>Role Management</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Форма создания роли */}
          <form onSubmit={handleCreateRole} className="mb-6 space-y-4">
            <div className="flex gap-4">
              <Input
                value={newRole.name}
                onChange={(e) => setNewRole({ ...newRole, name: e.target.value })}
                placeholder="Role name"
                className="flex-1"
              />
              <Input
                value={newRole.description || ''}
                onChange={(e) => setNewRole({ ...newRole, description: e.target.value })}
                placeholder="Description (optional)"
                className="flex-1"
              />
              <Button type="submit" disabled={createRoleMutation.isPending}>
                {createRoleMutation.isPending ? 'Creating...' : 'Create Role'}
              </Button>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </form>

          {/* Таблица ролей */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Users</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rolesData?.items.map((role: RoleResponse) => (
                <TableRow key={role.id}>
                  <TableCell>{role.name}</TableCell>
                  <TableCell>{role.description || '-'}</TableCell>
                  <TableCell>
                    <span className={role.is_active ? 'text-green-600' : 'text-red-600'}>
                      {role.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedRole(role)}
                        >
                          Manage Users ({role.users.length})
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                          <DialogTitle>Manage Users for {role.name}</DialogTitle>
                          <DialogDescription>
                            Add or remove users from this role
                          </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                          <div className="flex items-center gap-4">
                            <Input
                              value={userIds}
                              onChange={(e) => setUserIds(e.target.value)}
                              placeholder="User IDs (comma-separated)"
                            />
                            <Button
                              onClick={() => handleAssignUsers(role.id)}
                              disabled={assignUsersMutation.isPending}
                            >
                              Add Users
                            </Button>
                          </div>
                          <div className="mt-4">
                            <h4 className="mb-2 font-medium">Current Users:</h4>
                            <ul className="space-y-2">
                              {role.users.map((user) => (
                                <li key={user.id} className="flex items-center justify-between">
                                  <span>{user.username}</span>
                                  <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={() => handleRemoveUser(role.id, user.id)}
                                    disabled={removeUsersMutation.isPending}
                                  >
                                    Remove
                                  </Button>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </TableCell>
                  <TableCell>
                    {new Date(role.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeleteRole(role.id)}
                      disabled={deleteRoleMutation.isPending}
                    >
                      {deleteRoleMutation.isPending ? 'Deleting...' : 'Delete'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Пагинация */}
          {rolesData && (
            <div className="mt-4 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span>Rows per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                  className="border rounded p-1"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <span className="flex items-center">
                  Page {currentPage} of{' '}
                  {Math.ceil(rolesData.total / pageSize)}
                </span>
                <Button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= Math.ceil(rolesData.total / pageSize)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}