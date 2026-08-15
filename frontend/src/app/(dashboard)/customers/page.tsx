"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import {
  Users,
  Search,
  Plus,
  Download,
  Upload,
  RefreshCw,
  BarChart3,
  X,
  Edit2,
  Trash2,
  Mail,
  Phone,
  Globe,
  MapPin,
  Briefcase,
  User as UserIcon,
  ChevronLeft,
  ChevronRight,
  PlusCircle,
  FileText,
  Activity as ActivityIcon,
  Calendar,
  Sparkles,
  Archive,
  RotateCcw,
  MoreHorizontal,
  Eye
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type {
  CustomerRead,
  CustomerCreate,
  CustomerUpdate,
  CustomerListResponse,
  ContactRead,
  ContactCreate,
  CustomerAddressRead,
  CustomerAddressCreate,
  CustomerStatus,
  CustomerType,
  AddressType
} from "@/types/customer";

export default function CustomersPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Role permissions
  const isManager = user?.role === "manager" || user?.role === "admin";
  const isExecutive = user?.role === "executive";
  const isSalesRep = user?.role === "sales_rep";
  const isAdmin = user?.role === "admin";

  const canCreate = isManager || isSalesRep;
  const canImport = isManager;
  const canExport = isManager || isExecutive;
  const canSyncSalesforce = isManager;
  const canViewAnalytics = isManager || isExecutive;
  const canAssign = isManager;

  const canArchive = isManager;
  const canRestore = isManager;
  const canDelete = isAdmin;

  // Page, filter, and search states
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ACTIVE");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [industryFilter, setIndustryFilter] = useState<string>("");

  // UI Selection states
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "contacts" | "notes" | "quotes" | "activity">("overview");

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isAddContactModalOpen, setIsAddContactModalOpen] = useState(false);
  const [isAddAddressModalOpen, setIsAddAddressModalOpen] = useState(false);

  // Archive / Restore / Delete confirmation states
  const [archiveConfirmId, setArchiveConfirmId] = useState<number | null>(null);
  const [restoreConfirmId, setRestoreConfirmId] = useState<number | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  // Row action menu dropdown state (holds customer ID of active menu)
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);

  // Note text state (for mock session notes)
  const [noteText, setNoteText] = useState("");
  const [sessionNotes, setSessionNotes] = useState<Record<number, { id: number; text: string; date: string }[]>>({});

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Close menus on click outside
  useEffect(() => {
    const handleOutsideClick = () => setActiveMenuId(null);
    window.addEventListener("click", handleOutsideClick);
    return () => window.removeEventListener("click", handleOutsideClick);
  }, []);

  // ─── React Query Hooks ────────────────────────────────────────────────────────

  // Fetch Customers list
  const { data: customersData, isLoading, isError, error } = useQuery<CustomerListResponse>({
    queryKey: ["customers", page, statusFilter, typeFilter, industryFilter, debouncedSearch],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (statusFilter) params.append("status", statusFilter);
      if (typeFilter) params.append("customer_type", typeFilter);
      if (industryFilter) params.append("industry", industryFilter);
      
      const endpoint = debouncedSearch
        ? `/customers/search?q=${encodeURIComponent(debouncedSearch)}&${params.toString()}`
        : `/customers/?${params.toString()}`;
      
      return api.get<CustomerListResponse>(endpoint);
    },
    placeholderData: keepPreviousData
  });

  // Fetch Selected Customer Details
  const { data: selectedCustomer } = useQuery<CustomerRead>({
    queryKey: ["customer", selectedCustomerId],
    queryFn: () => api.get<CustomerRead>(`/customers/${selectedCustomerId}`),
    enabled: selectedCustomerId !== null,
  });

  // Create Customer Mutation
  const createCustomerMutation = useMutation({
    mutationFn: (newCustomer: CustomerCreate) => api.post<CustomerRead>("/customers/", newCustomer),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      setIsCreateModalOpen(false);
    }
  });

  // Update Customer Mutation
  const updateCustomerMutation = useMutation({
    mutationFn: (updated: { id: number; data: CustomerUpdate }) =>
      api.put<CustomerRead>(`/customers/${updated.id}`, updated.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customer", data.id] });
      setIsEditModalOpen(false);
    }
  });

  // Assign Customer Mutation
  const assignCustomerMutation = useMutation({
    mutationFn: (payload: { id: number; owner_id: string }) =>
      api.post<CustomerRead>(`/customers/${payload.id}/assign`, { owner_id: payload.owner_id }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customer", data.id] });
    }
  });

  // Archive Customer Mutation (Soft Delete)
  const archiveCustomerMutation = useMutation({
    mutationFn: (id: number) => api.patch<CustomerRead>(`/customers/${id}/archive`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customer", data.id] });
      setArchiveConfirmId(null);
    }
  });

  // Restore Customer Mutation
  const restoreCustomerMutation = useMutation({
    mutationFn: (id: number) => api.patch<CustomerRead>(`/customers/${id}/restore`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customer", data.id] });
      setRestoreConfirmId(null);
    }
  });

  // Permanent Delete Customer Mutation
  const deleteCustomerMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/customers/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      setSelectedCustomerId(null);
      setDeleteConfirmId(null);
    }
  });

  // Add Contact Mutation
  const addContactMutation = useMutation({
    mutationFn: (payload: { customerId: number; data: ContactCreate }) =>
      api.post<ContactRead>(`/customers/${payload.customerId}/contacts`, payload.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customer", selectedCustomerId] });
      setIsAddContactModalOpen(false);
    }
  });

  // Delete Contact Mutation
  const deleteContactMutation = useMutation({
    mutationFn: (contactId: number) =>
      api.delete(`/customers/${selectedCustomerId}/contacts/${contactId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customer", selectedCustomerId] });
    }
  });

  // Add Address Mutation
  const addAddressMutation = useMutation({
    mutationFn: (payload: { customerId: number; data: CustomerAddressCreate }) =>
      api.post<CustomerAddressRead>(`/customers/${payload.customerId}/addresses`, payload.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customer", selectedCustomerId] });
      setIsAddAddressModalOpen(false);
    }
  });

  // Delete Address Mutation
  const deleteAddressMutation = useMutation({
    mutationFn: (addressId: number) =>
      api.delete(`/customers/${selectedCustomerId}/addresses/${addressId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customer", selectedCustomerId] });
    }
  });

  // ─── Actions ─────────────────────────────────────────────────────────────────

  const handleCreateCustomer = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data: CustomerCreate = {
      customer_number: formData.get("customer_number") as string,
      legal_name: formData.get("legal_name") as string,
      display_name: (formData.get("display_name") as string) || null,
      email: (formData.get("email") as string) || null,
      phone: (formData.get("phone") as string) || null,
      website: (formData.get("website") as string) || null,
      industry: (formData.get("industry") as string) || null,
      customer_type: formData.get("customer_type") as CustomerType,
      status: formData.get("status") as CustomerStatus,
      owner_id: (formData.get("owner_id") as string) || null,
    };
    createCustomerMutation.mutate(data);
  };

  const handleUpdateCustomer = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedCustomer) return;
    const formData = new FormData(e.currentTarget);
    const data: CustomerUpdate = {
      customer_number: formData.get("customer_number") as string,
      legal_name: formData.get("legal_name") as string,
      display_name: (formData.get("display_name") as string) || null,
      email: (formData.get("email") as string) || null,
      phone: (formData.get("phone") as string) || null,
      website: (formData.get("website") as string) || null,
      industry: (formData.get("industry") as string) || null,
      customer_type: formData.get("customer_type") as CustomerType,
      status: formData.get("status") as CustomerStatus,
      owner_id: (formData.get("owner_id") as string) || null,
    };
    updateCustomerMutation.mutate({ id: selectedCustomer.id, data });
  };

  const handleAddContact = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedCustomerId) return;
    const formData = new FormData(e.currentTarget);
    const data: ContactCreate = {
      first_name: formData.get("first_name") as string,
      last_name: formData.get("last_name") as string,
      email: formData.get("email") as string,
      phone: (formData.get("phone") as string) || null,
      is_primary: formData.get("is_primary") === "true"
    };
    addContactMutation.mutate({ customerId: selectedCustomerId, data });
  };

  const handleAddAddress = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedCustomerId) return;
    const formData = new FormData(e.currentTarget);
    const data: CustomerAddressCreate = {
      address_type: formData.get("address_type") as AddressType,
      line1: formData.get("line1") as string,
      line2: (formData.get("line2") as string) || null,
      city: formData.get("city") as string,
      state: formData.get("state") as string,
      postal_code: formData.get("postal_code") as string,
      country: formData.get("country") as string,
      is_primary: formData.get("is_primary") === "true"
    };
    addAddressMutation.mutate({ customerId: selectedCustomerId, data });
  };

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !noteText.trim()) return;
    const newNote = {
      id: Date.now(),
      text: noteText,
      date: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    };
    setSessionNotes(prev => ({
      ...prev,
      [selectedCustomerId]: [newNote, ...(prev[selectedCustomerId] || [])]
    }));
    setNoteText("");
  };

  // Helper to extract initials
  const getAvatarInitials = (name: string) => {
    if (!name) return "??";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const activeNotes = selectedCustomerId ? sessionNotes[selectedCustomerId] || [] : [];

  return (
    <div className="flex gap-6 min-h-[calc(100vh-8rem)] relative select-none">
      
      {/* ─── LEFT SIDEBAR: CUSTOMERS TABLE ─── */}
      <div className={`flex-1 space-y-6 transition-all duration-300 ${selectedCustomerId ? "max-w-[65%]" : "max-w-full"}`}>
        
        {/* Header toolbar */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-1 flex items-center gap-2">
              <Users size={28} className="text-zinc-500" />
              <span>Customers</span>
            </h1>
            <p className="text-xs text-zinc-400">Manage and view your customer profiles</p>
          </div>
          
          <div className="flex items-center gap-2 flex-wrap">
            {canExport && (
              <button 
                className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                title="Export list (Coming Soon)"
              >
                <Download size={14} />
                <span>Export</span>
              </button>
            )}
            {canImport && (
              <button 
                className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                title="Import Excel (Coming Soon)"
              >
                <Upload size={14} />
                <span>Import Excel</span>
              </button>
            )}
            {canSyncSalesforce && (
              <button 
                className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                title="Salesforce Sync (Coming Soon)"
              >
                <RefreshCw size={14} />
                <span>Salesforce Sync</span>
              </button>
            )}
            {canViewAnalytics && (
              <button 
                className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                title="Analytics Dashboard (Coming Soon)"
              >
                <BarChart3 size={14} />
                <span>Analytics</span>
              </button>
            )}
            {canCreate && (
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center gap-1.5 bg-teal-500 text-zinc-950 px-4.5 py-2 rounded-lg text-xs font-extrabold hover:bg-teal-400 transition-colors shadow-lg shadow-teal-500/10"
              >
                <Plus size={14} />
                <span>New Customer</span>
              </button>
            )}
          </div>
        </div>

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row items-center gap-3 bg-zinc-900 border border-zinc-850 p-3 rounded-xl shadow-md">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={16} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search customers by name, email, phone..."
              className="w-full pl-9 pr-4 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-zinc-700 placeholder-zinc-650"
            />
          </div>
          
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-zinc-950 border border-zinc-850 text-zinc-300 text-xs rounded-lg px-2.5 py-2 focus:outline-none focus:border-zinc-700"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active Only</option>
              <option value="ARCHIVED">Archived Only</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-zinc-950 border border-zinc-850 text-zinc-300 text-xs rounded-lg px-2.5 py-2 focus:outline-none focus:border-zinc-700"
            >
              <option value="">Type: All</option>
              <option value="BUSINESS">Business</option>
              <option value="INDIVIDUAL">Individual</option>
            </select>
            
            {(statusFilter || typeFilter || searchQuery) && (
              <button
                onClick={() => {
                  setStatusFilter("");
                  setTypeFilter("");
                  setSearchQuery("");
                }}
                className="text-xs text-zinc-400 hover:text-zinc-100 font-medium px-2 py-1.5 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Loading / Error states */}
        {isLoading ? (
          <div className="border border-zinc-850 rounded-xl bg-zinc-900/30 p-24 text-center">
            <RefreshCw className="mx-auto text-teal-500 animate-spin mb-3" size={24} />
            <span className="text-sm text-zinc-400 font-medium">Fetching customer directory...</span>
          </div>
        ) : isError ? (
          <div className="border border-red-900/30 rounded-xl bg-red-950/10 p-12 text-center">
            <p className="text-sm text-red-400 font-semibold mb-2">Error loading customers</p>
            <p className="text-xs text-red-500">{(error as any)?.detail || "Check your network connection."}</p>
          </div>
        ) : !customersData || customersData.items.length === 0 ? (
          <div className="border border-zinc-850 rounded-xl bg-zinc-900/30 p-20 text-center">
            <Users size={40} className="mx-auto text-zinc-650 mb-3" />
            <h3 className="text-sm font-bold text-zinc-200 mb-1">No customers found</h3>
            <p className="text-xs text-zinc-500 max-w-xs mx-auto mb-4">
              Create a new customer profile or clear your search filters.
            </p>
            {canCreate && (
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="inline-flex items-center gap-1.5 bg-zinc-800 border border-zinc-750 text-zinc-200 px-3.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-zinc-750 hover:text-zinc-100 transition-colors"
              >
                <Plus size={12} />
                <span>Create Customer</span>
              </button>
            )}
          </div>
        ) : (
          <div className="border border-zinc-850 rounded-xl bg-zinc-900/35 overflow-hidden shadow-lg">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 text-[10px] uppercase font-bold text-zinc-500 bg-zinc-900/50">
                    <th className="px-5 py-3">Customer Name</th>
                    <th className="px-4 py-3">Industry</th>
                    <th className="px-4 py-3">Owner</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Created On</th>
                    <th className="px-4 py-3 w-[60px]"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-850 text-xs">
                  {customersData.items.map((cust) => (
                    <tr
                      key={cust.id}
                      onClick={() => {
                        setSelectedCustomerId(cust.id);
                        setActiveTab("overview");
                      }}
                      className={`hover:bg-zinc-800/40 cursor-pointer transition-colors ${selectedCustomerId === cust.id ? "bg-zinc-800/50" : ""} ${cust.status === "ARCHIVED" ? "opacity-60 bg-zinc-950/20" : ""}`}
                    >
                      <td className="px-5 py-3 flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700/60 flex items-center justify-center font-bold text-zinc-300 text-xs">
                          {getAvatarInitials(cust.legal_name)}
                        </div>
                        <div>
                          <div className={`font-semibold text-zinc-200 ${cust.status === "ARCHIVED" ? "line-through text-zinc-500" : ""}`}>
                            {cust.legal_name}
                          </div>
                          <div className="text-[10px] text-zinc-500">{cust.email || "No email"}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-zinc-400 font-medium">{cust.industry || "—"}</td>
                      <td className="px-4 py-3 text-zinc-400 font-medium">
                        <span className="inline-flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded-full bg-teal-950 border border-teal-800 text-teal-400 text-[8px] font-bold flex items-center justify-center">
                            {cust.owner_id ? "O" : "S"}
                          </span>
                          <span className="text-[11px] truncate max-w-[80px]">
                            {cust.owner_id ? cust.owner_id.slice(0, 8) : "System"}
                          </span>
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold uppercase tracking-wider ${
                          cust.status === "ACTIVE" ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/40" :
                          cust.status === "PROSPECT" ? "bg-amber-950/40 text-amber-400 border border-amber-800/40" :
                          cust.status === "INACTIVE" ? "bg-zinc-800 text-zinc-400 border border-zinc-750" :
                          "bg-red-955/40 text-red-400 border border-red-900/40"
                        }`}>
                          {cust.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-500">
                        {new Date(cust.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                      </td>
                      <td className="px-4 py-3 relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveMenuId(activeMenuId === cust.id ? null : cust.id);
                          }}
                          className="p-1 hover:bg-zinc-800 rounded-lg text-zinc-400 hover:text-zinc-200 transition-colors"
                        >
                          <MoreHorizontal size={16} />
                        </button>
                        
                        {/* Context Menu Dropdown */}
                        {activeMenuId === cust.id && (
                          <div 
                            onClick={(e) => e.stopPropagation()}
                            className="absolute right-4 mt-1.5 w-36 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl z-20 overflow-hidden divide-y divide-zinc-800"
                          >
                            <div className="py-1">
                              <button
                                onClick={() => {
                                  setSelectedCustomerId(cust.id);
                                  setActiveTab("overview");
                                  setActiveMenuId(null);
                                }}
                                className="flex items-center gap-2 w-full px-3 py-2 text-left text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                              >
                                <Eye size={12} />
                                <span>View Details</span>
                              </button>
                              {canCreate && (
                                <button
                                  onClick={() => {
                                    setSelectedCustomerId(cust.id);
                                    setIsEditModalOpen(true);
                                    setActiveMenuId(null);
                                  }}
                                  className="flex items-center gap-2 w-full px-3 py-2 text-left text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                                >
                                  <Edit2 size={12} />
                                  <span>Edit Profile</span>
                                </button>
                              )}
                            </div>
                            {isManager && (
                              <div className="py-1">
                                {cust.status !== "ARCHIVED" ? (
                                  <button
                                    onClick={() => {
                                      setArchiveConfirmId(cust.id);
                                      setActiveMenuId(null);
                                    }}
                                    className="flex items-center gap-2 w-full px-3 py-2 text-left text-zinc-400 hover:bg-zinc-800 hover:text-red-400 transition-colors"
                                  >
                                    <Archive size={12} />
                                    <span>Archive</span>
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => {
                                      setRestoreConfirmId(cust.id);
                                      setActiveMenuId(null);
                                    }}
                                    className="flex items-center gap-2 w-full px-3 py-2 text-left text-teal-400 hover:bg-zinc-800 hover:text-teal-350 transition-colors"
                                  >
                                    <RotateCcw size={12} />
                                    <span>Restore</span>
                                  </button>
                                )}
                              </div>
                            )}
                            {isAdmin && (
                              <div className="py-1">
                                <button
                                  onClick={() => {
                                    setDeleteConfirmId(cust.id);
                                    setActiveMenuId(null);
                                  }}
                                  className="flex items-center gap-2 w-full px-3 py-2 text-left text-red-500 hover:bg-zinc-800 hover:text-red-450 transition-colors"
                                >
                                  <Trash2 size={12} />
                                  <span>Delete Perm</span>
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="border-t border-zinc-850 p-4 flex items-center justify-between text-xs text-zinc-500 bg-zinc-900/20">
              <div>
                Showing <span className="font-semibold text-zinc-400">{(page - 1) * pageSize + 1}</span> to{" "}
                <span className="font-semibold text-zinc-400">
                  {Math.min(page * pageSize, customersData.total)}
                </span>{" "}
                of <span className="font-semibold text-zinc-400">{customersData.total}</span> customers
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft size={14} />
                </button>
                <span className="px-3 font-semibold text-zinc-300">
                  Page {page} of {customersData.pages || 1}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(p + 1, customersData.pages))}
                  disabled={page >= customersData.pages}
                  className="p-1.5 rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ─── RIGHT SIDEBAR: SELECTED CUSTOMER DETAILS ─── */}
      {selectedCustomerId && selectedCustomer && (
        <div className="w-[33%] bg-zinc-900/60 border border-zinc-850 rounded-2xl shadow-xl flex flex-col fixed top-32 right-8 bottom-8 z-10 overflow-hidden animate-in slide-in-from-right duration-250 backdrop-blur-xl">
          
          {/* Detail Header */}
          <div className="p-4 border-b border-zinc-850 flex items-center justify-between bg-zinc-900/80">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${selectedCustomer.status === "ACTIVE" ? "bg-emerald-400 animate-pulse" : "bg-zinc-650"}`} />
              <h2 className={`font-bold text-zinc-100 truncate max-w-[150px] ${selectedCustomer.status === "ARCHIVED" ? "line-through text-zinc-550" : ""}`}>{selectedCustomer.legal_name}</h2>
              {selectedCustomer.status === "ARCHIVED" && (
                <span className="px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase bg-red-955/30 text-red-400 border border-red-900/30">Archived</span>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              {isManager && (
                selectedCustomer.status !== "ARCHIVED" ? (
                  <button
                    onClick={() => setArchiveConfirmId(selectedCustomer.id)}
                    className="p-1 text-zinc-400 hover:text-red-400 hover:bg-zinc-800 rounded transition-colors"
                    title="Archive customer"
                  >
                    <Archive size={14} />
                  </button>
                ) : (
                  <button
                    onClick={() => setRestoreConfirmId(selectedCustomer.id)}
                    className="p-1 text-zinc-400 hover:text-teal-400 hover:bg-zinc-800 rounded transition-colors"
                    title="Restore customer"
                  >
                    <RotateCcw size={14} />
                  </button>
                )
              )}
              <button
                onClick={() => setSelectedCustomerId(null)}
                className="p-1 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-850 rounded-lg transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-zinc-850 bg-zinc-900/40 text-[11px] font-semibold text-zinc-400 font-sans">
            {(["overview", "contacts", "notes", "quotes", "activity"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-3 text-center border-b-2 capitalize transition-colors ${
                  activeTab === tab
                    ? "border-teal-400 text-teal-400 bg-zinc-850/20"
                    : "border-transparent hover:text-zinc-200"
                }`}
              >
                {tab === "contacts" ? `Contacts (${selectedCustomer.contacts.length})` : tab}
              </button>
            ))}
          </div>

          {/* Detail Tab Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            
            {/* OVERVIEW TAB */}
            {activeTab === "overview" && (
              <div className="space-y-6">
                
                {/* Customer Information Card */}
                <div className="space-y-4 bg-zinc-900/45 p-4 rounded-xl border border-zinc-850">
                  <div className="flex justify-between items-center pb-2 border-b border-zinc-800">
                    <h3 className="text-xs font-bold text-zinc-300">Customer Info</h3>
                    {canCreate && selectedCustomer.status !== "ARCHIVED" && (
                      <button
                        onClick={() => setIsEditModalOpen(true)}
                        className="p-1 text-zinc-500 hover:text-teal-400 rounded transition-colors"
                      >
                        <Edit2 size={12} />
                      </button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-y-3.5 gap-x-2 text-xs">
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Email</div>
                      <div className="text-zinc-300 truncate font-medium flex items-center gap-1.5">
                        <Mail size={12} className="text-zinc-650" />
                        <span>{selectedCustomer.email || "—"}</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Website</div>
                      <div className="text-zinc-300 truncate font-medium flex items-center gap-1.5">
                        <Globe size={12} className="text-zinc-650" />
                        <span>{selectedCustomer.website || "—"}</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Phone</div>
                      <div className="text-zinc-300 truncate font-medium flex items-center gap-1.5">
                        <Phone size={12} className="text-zinc-650" />
                        <span>{selectedCustomer.phone || "—"}</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Industry</div>
                      <div className="text-zinc-300 truncate font-medium flex items-center gap-1.5">
                        <Briefcase size={12} className="text-zinc-650" />
                        <span>{selectedCustomer.industry || "—"}</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Owner</div>
                      <div className="text-zinc-300 truncate font-medium flex items-center gap-1.5">
                        <UserIcon size={12} className="text-zinc-650" />
                        <span>{selectedCustomer.owner_id ? selectedCustomer.owner_id.slice(0, 8) : "Unassigned"}</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Status</div>
                      <div>
                        <span className={`px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase border ${
                          selectedCustomer.status === "ACTIVE" ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/40" : "bg-red-955/40 text-red-400 border-red-900/40"
                        }`}>
                          {selectedCustomer.status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Billing Address Card */}
                <div className="space-y-3 bg-zinc-900/45 p-4 rounded-xl border border-zinc-850">
                  <div className="flex justify-between items-center pb-2 border-b border-zinc-800">
                    <h3 className="text-xs font-bold text-zinc-300">Billing Address</h3>
                    {canCreate && selectedCustomer.status !== "ARCHIVED" && (
                      <button
                        onClick={() => setIsAddAddressModalOpen(true)}
                        className="p-1 text-zinc-500 hover:text-teal-400 rounded transition-colors"
                      >
                        <PlusCircle size={12} />
                      </button>
                    )}
                  </div>
                  
                  {selectedCustomer.addresses.length > 0 ? (
                    selectedCustomer.addresses.map((addr) => (
                      <div key={addr.id} className="text-xs space-y-1 text-zinc-400">
                        <div className="font-semibold text-zinc-300 flex items-center gap-1.5">
                          <MapPin size={12} className="text-zinc-650" />
                          <span>{addr.address_type} Address {addr.is_primary && "(Primary)"}</span>
                        </div>
                        <div className="pl-4.5">{addr.line1}</div>
                        {addr.line2 && <div className="pl-4.5">{addr.line2}</div>}
                        <div className="pl-4.5">{addr.city}, {addr.state} {addr.postal_code}</div>
                        <div className="pl-4.5">{addr.country}</div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-zinc-600 pl-1">No addresses recorded</div>
                  )}
                </div>

                {/* Customer Summary Card */}
                <div className="space-y-4 bg-zinc-900/45 p-4 rounded-xl border border-zinc-850">
                  <h3 className="text-xs font-bold text-zinc-300 pb-2 border-b border-zinc-800">Customer Summary</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800">
                      <div className="text-[10px] text-zinc-550 font-bold uppercase tracking-wider mb-1">Total Quotes</div>
                      <div className="text-lg font-bold text-zinc-200">0</div>
                    </div>
                    <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800">
                      <div className="text-[10px] text-zinc-550 font-bold uppercase tracking-wider mb-1">Total Value</div>
                      <div className="text-lg font-bold text-zinc-200">$0.00</div>
                    </div>
                  </div>
                </div>

                <div className="text-[10px] text-zinc-650 space-y-1 pl-1.5">
                  <div>Created: {new Date(selectedCustomer.created_at).toLocaleString()}</div>
                  <div>Updated: {new Date(selectedCustomer.updated_at).toLocaleString()}</div>
                  {selectedCustomer.deleted_at && (
                    <div className="text-red-400 font-medium">
                      Archived: {new Date(selectedCustomer.deleted_at).toLocaleString()} 
                      {selectedCustomer.deleted_by && ` by ${selectedCustomer.deleted_by.slice(0, 8)}`}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* CONTACTS TAB */}
            {activeTab === "contacts" && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-xs font-bold text-zinc-300">Contacts List</h3>
                  {canCreate && selectedCustomer.status !== "ARCHIVED" && (
                    <button
                      onClick={() => setIsAddContactModalOpen(true)}
                      className="text-xs text-teal-400 hover:text-teal-300 font-bold flex items-center gap-1"
                    >
                      <Plus size={14} />
                      <span>Add Contact</span>
                    </button>
                  )}
                </div>

                {selectedCustomer.contacts.length > 0 ? (
                  <div className="space-y-3">
                    {selectedCustomer.contacts.map((contact) => (
                      <div key={contact.id} className="p-3 bg-zinc-950 border border-zinc-850 rounded-xl flex items-start justify-between">
                        <div>
                          <div className="text-xs font-bold text-zinc-200 flex items-center gap-1.5">
                            <span>{contact.first_name} {contact.last_name}</span>
                            {contact.is_primary && (
                              <span className="bg-teal-950/40 text-teal-400 text-[8px] px-1 py-0.5 rounded border border-teal-850">Primary</span>
                            )}
                          </div>
                          <div className="text-[10px] text-zinc-500 mt-1 flex items-center gap-1"><Mail size={10} /> {contact.email}</div>
                          {contact.phone && (
                            <div className="text-[10px] text-zinc-500 flex items-center gap-1"><Phone size={10} /> {contact.phone}</div>
                          )}
                        </div>
                        {isManager && selectedCustomer.status !== "ARCHIVED" && (
                          <button
                            onClick={() => deleteContactMutation.mutate(contact.id)}
                            className="p-1 text-zinc-650 hover:text-red-400 rounded transition-colors"
                            title="Delete Stakeholder"
                          >
                            <Trash2 size={12} />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-xs text-zinc-600">No stakeholder contacts recorded.</div>
                )}
              </div>
            )}

            {/* NOTES TAB */}
            {activeTab === "notes" && (
              <div className="space-y-4">
                <h3 className="text-xs font-bold text-zinc-300">Customer Session Notes</h3>
                
                {selectedCustomer.status !== "ARCHIVED" ? (
                  <form onSubmit={handleAddNote} className="space-y-2">
                    <textarea
                      value={noteText}
                      onChange={(e) => setNoteText(e.target.value)}
                      placeholder="Write a session note (saved locally)..."
                      className="w-full p-2.5 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-300 focus:outline-none focus:border-zinc-700 min-h-[60px]"
                    />
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        className="bg-teal-500 text-zinc-950 px-3 py-1.5 rounded text-xs font-bold hover:bg-teal-400 transition-colors"
                      >
                        Post Note
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="p-3 bg-zinc-950/40 border border-zinc-850 rounded-lg text-xs text-zinc-550 font-medium text-center">
                    Note submission disabled for archived accounts.
                  </div>
                )}

                {activeNotes.length > 0 ? (
                  <div className="space-y-3 mt-4">
                    {activeNotes.map((note) => (
                      <div key={note.id} className="p-3 bg-zinc-950/60 border border-zinc-850 rounded-lg space-y-1.5">
                        <div className="text-xs text-zinc-300 font-medium">{note.text}</div>
                        <div className="text-[9px] text-zinc-650 flex items-center gap-1 font-semibold">
                          <Calendar size={8} />
                          <span>{note.date}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-xs text-zinc-600">No notes written during this session.</div>
                )}
              </div>
            )}

            {/* QUOTES TAB */}
            {activeTab === "quotes" && (
              <div className="space-y-4">
                <h3 className="text-xs font-bold text-zinc-300">Quote Pipeline</h3>
                <div className="border border-zinc-850 rounded-xl bg-zinc-950 p-8 text-center">
                  <FileText size={24} className="mx-auto text-zinc-700 mb-2" />
                  <div className="text-xs font-semibold text-zinc-400">No quotes generated yet</div>
                  <p className="text-[10px] text-zinc-650 mt-1 max-w-[200px] mx-auto">
                    To start pricing, build a new configuration in the Quote Builder.
                  </p>
                </div>
              </div>
            )}

            {/* ACTIVITY TAB */}
            {activeTab === "activity" && (
              <div className="space-y-4">
                <h3 className="text-xs font-bold text-zinc-300">Audit Trail / Activity</h3>
                <div className="space-y-4 relative pl-4 border-l border-zinc-800 text-xs">
                  <div className="relative">
                    <span className="absolute -left-[21px] top-0.5 w-2 h-2 rounded-full bg-teal-500" />
                    <div className="font-bold text-zinc-300">Profile Loaded</div>
                    <div className="text-[9px] text-zinc-550 mt-0.5">System • Just Now</div>
                  </div>
                  {selectedCustomer.deleted_at && (
                    <div className="relative">
                      <span className="absolute -left-[21px] top-0.5 w-2 h-2 rounded-full bg-red-400" />
                      <div className="font-bold text-red-400">Customer Archived</div>
                      <div className="text-[9px] text-zinc-550 mt-0.5">
                        {selectedCustomer.deleted_by ? `By user: ${selectedCustomer.deleted_by.slice(0, 8)}` : "System"} • {new Date(selectedCustomer.deleted_at).toLocaleDateString()}
                      </div>
                    </div>
                  )}
                  <div className="relative">
                    <span className="absolute -left-[21px] top-0.5 w-2 h-2 rounded-full bg-zinc-700" />
                    <div className="font-bold text-zinc-400">Account Registered</div>
                    <div className="text-[9px] text-zinc-550 mt-0.5">
                      {selectedCustomer.owner_id ? `Owner ID: ${selectedCustomer.owner_id.slice(0, 8)}` : "System"} • {new Date(selectedCustomer.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── MODAL: CREATE CUSTOMER ─── */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-zinc-850">
              <h2 className="text-base font-bold text-zinc-100 flex items-center gap-1.5">
                <Users size={18} className="text-zinc-500" />
                <span>Onboard New Customer</span>
              </h2>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="p-1 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-800 rounded transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateCustomer} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Customer Number *</label>
                  <input
                    type="text"
                    name="customer_number"
                    required
                    placeholder="e.g. CUST-1002"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Legal Name *</label>
                  <input
                    type="text"
                    name="legal_name"
                    required
                    placeholder="e.g. Acme Corp"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Display Name</label>
                  <input
                    type="text"
                    name="display_name"
                    placeholder="e.g. Acme"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Email Address</label>
                  <input
                    type="email"
                    name="email"
                    placeholder="contact@company.com"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Phone Number</label>
                  <input
                    type="text"
                    name="phone"
                    placeholder="+1 555-0199"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Website URL</label>
                  <input
                    type="text"
                    name="website"
                    placeholder="www.company.com"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Industry</label>
                  <input
                    type="text"
                    name="industry"
                    placeholder="e.g. Technology, Retail"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Owner ID (UUID)</label>
                  <input
                    type="text"
                    name="owner_id"
                    defaultValue={user?.id || ""}
                    readOnly={!canAssign}
                    placeholder="Owner User UUID"
                    className={`w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700 ${!canAssign ? "opacity-60 cursor-not-allowed" : ""}`}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Customer Type</label>
                  <select
                    name="customer_type"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  >
                    <option value="BUSINESS">Business</option>
                    <option value="INDIVIDUAL">Individual</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Status</label>
                  <select
                    name="status"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  >
                    <option value="PROSPECT">Prospect</option>
                    <option value="ACTIVE">Active</option>
                    <option value="INACTIVE">Inactive</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-zinc-850">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-semibold hover:bg-zinc-750 hover:text-zinc-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-teal-500 text-zinc-950 px-5 py-2 rounded-lg font-bold hover:bg-teal-400 transition-colors"
                >
                  Submit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: EDIT CUSTOMER ─── */}
      {isEditModalOpen && selectedCustomer && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-zinc-850">
              <h2 className="text-base font-bold text-zinc-100 flex items-center gap-1.5">
                <Edit2 size={16} className="text-zinc-500" />
                <span>Modify Customer Account</span>
              </h2>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="p-1 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-800 rounded transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleUpdateCustomer} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Customer Number *</label>
                  <input
                    type="text"
                    name="customer_number"
                    defaultValue={selectedCustomer.customer_number}
                    required
                    placeholder="e.g. CUST-1002"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Legal Name *</label>
                  <input
                    type="text"
                    name="legal_name"
                    defaultValue={selectedCustomer.legal_name}
                    required
                    placeholder="e.g. Acme Corp"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Display Name</label>
                  <input
                    type="text"
                    name="display_name"
                    defaultValue={selectedCustomer.display_name || ""}
                    placeholder="e.g. Acme"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Email Address</label>
                  <input
                    type="email"
                    name="email"
                    defaultValue={selectedCustomer.email || ""}
                    placeholder="contact@company.com"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Phone Number</label>
                  <input
                    type="text"
                    name="phone"
                    defaultValue={selectedCustomer.phone || ""}
                    placeholder="+1 555-0199"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Website URL</label>
                  <input
                    type="text"
                    name="website"
                    defaultValue={selectedCustomer.website || ""}
                    placeholder="www.company.com"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Industry</label>
                  <input
                    type="text"
                    name="industry"
                    defaultValue={selectedCustomer.industry || ""}
                    placeholder="e.g. Technology, Retail"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Owner ID (UUID)</label>
                  <input
                    type="text"
                    name="owner_id"
                    defaultValue={selectedCustomer.owner_id || ""}
                    readOnly={!canAssign}
                    placeholder="Owner User UUID"
                    className={`w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700 ${!canAssign ? "opacity-60 cursor-not-allowed" : ""}`}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Customer Type</label>
                  <select
                    name="customer_type"
                    defaultValue={selectedCustomer.customer_type}
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  >
                    <option value="BUSINESS">Business</option>
                    <option value="INDIVIDUAL">Individual</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Status</label>
                  <select
                    name="status"
                    defaultValue={selectedCustomer.status}
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-700"
                  >
                    <option value="PROSPECT">Prospect</option>
                    <option value="ACTIVE">Active</option>
                    <option value="INACTIVE">Inactive</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-zinc-850">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-semibold hover:bg-zinc-750 hover:text-zinc-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-teal-500 text-zinc-950 px-5 py-2 rounded-lg font-bold hover:bg-teal-400 transition-colors"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: ADD CONTACT ─── */}
      {isAddContactModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-sm p-5 shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-zinc-850">
              <h2 className="text-sm font-bold text-zinc-100">Add Stakeholder Contact</h2>
              <button onClick={() => setIsAddContactModalOpen(false)} className="text-zinc-500 hover:text-zinc-100"><X size={16} /></button>
            </div>
            
            <form onSubmit={handleAddContact} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">First Name *</label>
                  <input type="text" name="first_name" required className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Last Name *</label>
                  <input type="text" name="last_name" required className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
                </div>
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-zinc-400">Email Address *</label>
                <input type="email" name="email" required className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-zinc-400">Phone</label>
                <input type="text" name="phone" className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-zinc-400">Is Primary Representative?</label>
                <select name="is_primary" className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none">
                  <option value="false">No</option>
                  <option value="true">Yes</option>
                </select>
              </div>
              <div className="flex justify-end gap-2.5 pt-3 border-t border-zinc-850">
                <button type="button" onClick={() => setIsAddContactModalOpen(false)} className="bg-zinc-800 text-zinc-300 px-3.5 py-1.5 rounded-lg font-semibold hover:bg-zinc-750">Cancel</button>
                <button type="submit" className="bg-teal-500 text-zinc-950 px-4.5 py-1.5 rounded-lg font-bold hover:bg-teal-400">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: ADD ADDRESS ─── */}
      {isAddAddressModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-sm p-5 shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-zinc-850">
              <h2 className="text-sm font-bold text-zinc-100">Add Address record</h2>
              <button onClick={() => setIsAddAddressModalOpen(false)} className="text-zinc-500 hover:text-zinc-100"><X size={16} /></button>
            </div>
            
            <form onSubmit={handleAddAddress} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Address Type</label>
                  <select name="address_type" className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none">
                    <option value="BILLING">Billing Address</option>
                    <option value="SHIPPING">Shipping Address</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Is Primary Address?</label>
                  <select name="is_primary" className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none">
                    <option value="false">No</option>
                    <option value="true">Yes</option>
                  </select>
                </div>
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-zinc-400">Line 1 *</label>
                <input type="text" name="line1" required className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-zinc-400">Line 2</label>
                <input type="text" name="line2" className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">City *</label>
                  <input type="text" name="city" required className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">State *</label>
                  <input type="text" name="state" required className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Postal Code *</label>
                  <input type="text" name="postal_code" required className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-400">Country *</label>
                  <input type="text" name="country" required className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none" />
                </div>
              </div>
              <div className="flex justify-end gap-2.5 pt-3 border-t border-zinc-850">
                <button type="button" onClick={() => setIsAddAddressModalOpen(false)} className="bg-zinc-800 text-zinc-300 px-3.5 py-1.5 rounded-lg font-semibold hover:bg-zinc-750">Cancel</button>
                <button type="submit" className="bg-teal-500 text-zinc-950 px-4.5 py-1.5 rounded-lg font-bold hover:bg-teal-400">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── CONFIRMATION MODAL: ARCHIVE CUSTOMER ─── */}
      {archiveConfirmId !== null && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-sm p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-zinc-100">Archive Customer?</h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Archived customers will no longer appear in active customer lists, but their historical records (quotes, addresses, activities) will be preserved in the system.
            </p>
            <div className="flex justify-end gap-2.5 pt-2 border-t border-zinc-800">
              <button
                type="button"
                onClick={() => setArchiveConfirmId(null)}
                className="bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-semibold hover:bg-zinc-750 text-xs transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => archiveCustomerMutation.mutate(archiveConfirmId)}
                className="bg-red-500 text-zinc-950 px-5 py-2 rounded-lg font-bold hover:bg-red-400 text-xs transition-colors"
              >
                Archive Customer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── CONFIRMATION MODAL: RESTORE CUSTOMER ─── */}
      {restoreConfirmId !== null && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-sm p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-zinc-100">Restore Customer?</h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Restoring this customer will set their status back to ACTIVE, allowing them to appear in active directories, quote building pipelines, and workflows.
            </p>
            <div className="flex justify-end gap-2.5 pt-2 border-t border-zinc-800">
              <button
                type="button"
                onClick={() => setRestoreConfirmId(null)}
                className="bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-semibold hover:bg-zinc-750 text-xs transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => restoreCustomerMutation.mutate(restoreConfirmId)}
                className="bg-teal-500 text-zinc-950 px-5 py-2 rounded-lg font-bold hover:bg-teal-400 text-xs transition-colors"
              >
                Restore Customer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── CONFIRMATION MODAL: PERMANENT DELETE ─── */}
      {deleteConfirmId !== null && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-sm p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-red-400">Permanently Delete Customer?</h2>
            <p className="text-xs text-zinc-450 leading-relaxed">
              <span className="font-bold text-red-500">WARNING:</span> This action is irreversible. It will permanently purge this customer and all associated contacts/addresses from the database.
            </p>
            <div className="flex justify-end gap-2.5 pt-2 border-t border-zinc-800">
              <button
                type="button"
                onClick={() => setDeleteConfirmId(null)}
                className="bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-semibold hover:bg-zinc-750 text-xs transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => deleteCustomerMutation.mutate(deleteConfirmId)}
                className="bg-red-650 text-zinc-100 px-5 py-2 rounded-lg font-bold hover:bg-red-550 text-xs transition-colors"
              >
                Permanently Delete
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
