"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import {
  BookOpen,
  Search,
  Plus,
  Download,
  Upload,
  RefreshCw,
  X,
  Edit2,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Archive,
  RotateCcw,
  MoreHorizontal,
  Eye,
  Laptop,
  Coins,
  Database,
  Sliders,
  DollarSign,
  Package,
  Layers,
  Settings,
  HelpCircle,
  Activity,
  Calendar,
  Grid,
  List as ListIcon,
  Filter,
  CheckSquare,
  Square,
  AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type {
  ProductRead,
  ProductCreate,
  ProductUpdate,
  CategoryRead,
  PriceBookRead
} from "@/types/catalog";

export default function ProductCatalogPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Role permissions
  const isManager = user?.role === "manager" || user?.role === "admin";
  const isExecutive = user?.role === "executive";
  const isSalesRep = user?.role === "sales_rep";
  const isAdmin = user?.role === "admin";

  const canCreate = isManager || isSalesRep;
  const canUpdate = isManager || isSalesRep;
  const canArchive = isManager;
  const canRestore = isManager;
  const canDelete = isAdmin;
  const canImport = isManager;
  const canViewCost = isManager || isExecutive;
  const canManageCost = isManager;
  const canViewMargin = isManager || isExecutive;

  // Pagination, search, and filter states
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  
  // Advanced filters from Left panel
  const [selectedCategories, setSelectedCategories] = useState<number[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ACTIVE"); // default view: Active products
  const [productTypeFilter, setProductTypeFilter] = useState<string>("ALL");
  const [selectedPriceBookId, setSelectedPriceBookId] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<string>("created_newest");

  // Selection & Details panel
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "pricing" | "specs">("overview");

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [archiveConfirmId, setArchiveConfirmId] = useState<number | null>(null);
  const [restoreConfirmId, setRestoreConfirmId] = useState<number | null>(null);

  // Excel Import states
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<{
    total_rows: number;
    imported_count: number;
    failed_count: number;
    errors: { row: number; sku?: string; error: string }[];
  } | null>(null);

  // Row context menu state
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);

  // Layout View toggle
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Click outside listener for row context menu
  useEffect(() => {
    const handleOutsideClick = () => setActiveMenuId(null);
    window.addEventListener("click", handleOutsideClick);
    return () => window.removeEventListener("click", handleOutsideClick);
  }, []);

  // ─── React Query APIs ────────────────────────────────────────────────────────

  // Fetch Categories
  const { data: categories = [] } = useQuery<CategoryRead[]>({
    queryKey: ["categories"],
    queryFn: () => api.get<CategoryRead[]>("/categories"),
  });

  // Fetch Price Books
  const { data: priceBooks = [] } = useQuery<PriceBookRead[]>({
    queryKey: ["price-books"],
    queryFn: () => api.get<PriceBookRead[]>("/price-books"),
  });

  // Fetch Products
  const { data: products = [], isLoading, isError, error } = useQuery<ProductRead[]>({
    queryKey: ["products", page, statusFilter, selectedCategories, debouncedSearch],
    queryFn: async () => {
      const offset = (page - 1) * pageSize;
      const params = new URLSearchParams({
        offset: offset.toString(),
        limit: pageSize.toString(),
      });
      if (selectedCategories.length > 0) {
        params.append("category_id", selectedCategories[0].toString());
      }
      return api.get<ProductRead[]>(`/products?${params.toString()}`);
    },
    placeholderData: keepPreviousData
  });

  // Fetch Single Product Details
  const { data: selectedProduct } = useQuery<ProductRead>({
    queryKey: ["product", selectedProductId],
    queryFn: () => api.get<ProductRead>(`/products/${selectedProductId}`),
    enabled: selectedProductId !== null,
  });

  const selCostNum = selectedProduct?.cost_price !== undefined && selectedProduct?.cost_price !== null ? (typeof selectedProduct.cost_price === "string" ? parseFloat(selectedProduct.cost_price) : selectedProduct.cost_price) : null;
  const selMarginPercentNum = selectedProduct?.margin_percentage !== undefined && selectedProduct?.margin_percentage !== null ? (typeof selectedProduct.margin_percentage === "string" ? parseFloat(selectedProduct.margin_percentage) : selectedProduct.margin_percentage) : null;
  const selMarginAmtNum = selectedProduct?.margin_amount !== undefined && selectedProduct?.margin_amount !== null ? (typeof selectedProduct.margin_amount === "string" ? parseFloat(selectedProduct.margin_amount) : selectedProduct.margin_amount) : null;

  // Create Product Mutation
  const createProductMutation = useMutation({
    mutationFn: (newProd: ProductCreate) => api.post<ProductRead>("/products", newProd),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      setIsCreateModalOpen(false);
    }
  });

  // Edit Product Mutation
  const editProductMutation = useMutation({
    mutationFn: (payload: { id: number; data: ProductUpdate }) => 
      api.put<ProductRead>(`/products/${payload.id}`, payload.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product", data.id] });
      setIsEditModalOpen(false);
    }
  });

  // Archive Product Mutation
  const archiveProductMutation = useMutation({
    mutationFn: (id: number) => api.patch<ProductRead>(`/products/${id}/archive`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product", data.id] });
      setArchiveConfirmId(null);
    }
  });

  // Restore Product Mutation
  const restoreProductMutation = useMutation({
    mutationFn: (id: number) => api.patch<ProductRead>(`/products/${id}/restore`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product", data.id] });
      setRestoreConfirmId(null);
    }
  });

  // Excel Product Import Mutation
  const importProductsMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.upload<{
        total_rows: number;
        imported_count: number;
        failed_count: number;
        errors: { row: number; sku?: string; error: string }[];
      }>("/products/import", formData);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      setImportResult(data);
    }
  });

  // ─── Filter & Search Helpers ──────────────────────────────────────────────────

  const processedProducts = React.useMemo(() => {
    let list = [...products];

    if (debouncedSearch.trim() !== "") {
      const q = debouncedSearch.toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.sku.toLowerCase().includes(q) ||
          (p.description && p.description.toLowerCase().includes(q)) ||
          (p.external_crm_id && p.external_crm_id.toLowerCase().includes(q))
      );
    }

    if (selectedCategories.length > 0) {
      list = list.filter((p) => p.category_id && selectedCategories.includes(p.category_id));
    }

    if (statusFilter === "ACTIVE") {
      list = list.filter((p) => p.is_active);
    } else if (statusFilter === "INACTIVE") {
      list = list.filter((p) => !p.is_active);
    }

    if (productTypeFilter !== "ALL") {
      list = list.filter((p) => {
        const skuUpper = p.sku.toUpperCase();
        if (productTypeFilter === "SERVICE") return skuUpper.includes("SVC") || skuUpper.includes("SUP");
        if (productTypeFilter === "BUNDLE") return skuUpper.includes("BNDL");
        return !skuUpper.includes("SVC") && !skuUpper.includes("SUP") && !skuUpper.includes("BNDL");
      });
    }

    list.sort((a, b) => {
      if (sortBy === "created_newest") return b.id - a.id;
      if (sortBy === "created_oldest") return a.id - b.id;
      if (sortBy === "sku_asc") return a.sku.localeCompare(b.sku);
      if (sortBy === "sku_desc") return b.sku.localeCompare(a.sku);
      if (sortBy === "price_asc") return a.base_price - b.base_price;
      if (sortBy === "price_desc") return b.base_price - a.base_price;
      return 0;
    });

    return list;
  }, [products, debouncedSearch, selectedCategories, statusFilter, productTypeFilter, sortBy]);

  const handleToggleCategory = (catId: number) => {
    setSelectedCategories((prev) =>
      prev.includes(catId) ? prev.filter((id) => id !== catId) : [...prev, catId]
    );
    setPage(1);
  };

  const getProductTypeInfo = (sku: string) => {
    const skuUpper = sku.toUpperCase();
    if (skuUpper.includes("SVC") || skuUpper.includes("SUP")) {
      return { label: "Service", colorClass: "bg-purple-950/40 text-purple-400 border border-purple-800/40" };
    }
    if (skuUpper.includes("BNDL")) {
      return { label: "Bundle", colorClass: "bg-amber-955/40 text-amber-400 border border-amber-900/40" };
    }
    return { label: "Product", colorClass: "bg-blue-950/40 text-blue-400 border border-blue-800/40" };
  };

  const getProductIcon = (sku: string) => {
    const type = getProductTypeInfo(sku).label;
    if (type === "Service") return <HelpCircle size={14} className="text-purple-400" />;
    if (type === "Bundle") return <Package size={14} className="text-amber-400" />;
    return <Laptop size={14} className="text-blue-400" />;
  };

  const handleCreateProductSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const costVal = formData.get("cost_price") as string;
    const payload: ProductCreate = {
      sku: formData.get("sku") as string,
      name: formData.get("name") as string,
      description: (formData.get("description") as string) || null,
      base_price: parseFloat(formData.get("base_price") as string) || 0,
      cost_price: costVal ? parseFloat(costVal) : null,
      currency: "USD",
      is_active: formData.get("is_active") === "true",
      billing_type: (formData.get("billing_type") as "MRC" | "NRC" | "USAGE") || "MRC",
      category_id: formData.get("category_id") ? parseInt(formData.get("category_id") as string) : null,
      external_crm_id: (formData.get("external_crm_id") as string) || null,
    };
    createProductMutation.mutate(payload);
  };

  const handleEditProductSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedProduct) return;
    const formData = new FormData(e.currentTarget);
    const costVal = formData.get("cost_price") as string;
    const payload: ProductUpdate = {
      sku: formData.get("sku") as string,
      name: formData.get("name") as string,
      description: (formData.get("description") as string) || null,
      base_price: parseFloat(formData.get("base_price") as string) || 0,
      cost_price: costVal ? parseFloat(costVal) : null,
      currency: "USD",
      is_active: formData.get("is_active") === "true",
      billing_type: (formData.get("billing_type") as "MRC" | "NRC" | "USAGE") || undefined,
      category_id: formData.get("category_id") ? parseInt(formData.get("category_id") as string) : null,
      external_crm_id: (formData.get("external_crm_id") as string) || null,
    };
    editProductMutation.mutate({ id: selectedProduct.id, data: payload });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setImportResult(null);
    }
  };

  const triggerUpload = () => {
    if (selectedFile) {
      importProductsMutation.mutate(selectedFile);
    }
  };

  return (
    <div className="flex gap-6 min-h-[calc(100vh-8rem)] relative select-none">
      
      {/* ─── LEFT PANEL: CATEGORIES & STATUS FILTERS ─── */}
      <div className="w-[18%] bg-zinc-950/20 border border-zinc-850 p-4.5 rounded-xl space-y-6 shrink-0 h-fit">
        
        {/* Categories section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-zinc-300 uppercase tracking-wider">
            <span>Categories</span>
            <span className="text-[10px] text-zinc-550 lowercase font-medium">{categories.length} loaded</span>
          </div>
          <div className="space-y-2">
            <button
              onClick={() => setSelectedCategories([])}
              className="flex items-center gap-2 text-xs font-semibold w-full text-left"
            >
              {selectedCategories.length === 0 ? (
                <CheckSquare size={14} className="text-teal-400" />
              ) : (
                <Square size={14} className="text-zinc-600" />
              )}
              <span className={selectedCategories.length === 0 ? "text-zinc-200" : "text-zinc-450"}>All Categories</span>
            </button>
            {categories.map((cat) => {
              const isSelected = selectedCategories.includes(cat.id);
              return (
                <button
                  key={cat.id}
                  onClick={() => handleToggleCategory(cat.id)}
                  className="flex items-center gap-2 text-xs font-medium w-full text-left pl-1"
                >
                  {isSelected ? (
                    <CheckSquare size={13} className="text-teal-500" />
                  ) : (
                    <Square size={13} className="text-zinc-650" />
                  )}
                  <span className={isSelected ? "text-zinc-300" : "text-zinc-500"}>{cat.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Status Section */}
        <div className="space-y-3 pt-4 border-t border-zinc-850/50">
          <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Status</div>
          <div className="space-y-2">
            {[
              { val: "ALL", label: "All Statuses" },
              { val: "ACTIVE", label: "Active Only" },
              { val: "INACTIVE", label: "Inactive Only" }
            ].map((st) => {
              const isSelected = statusFilter === st.val;
              return (
                <button
                  key={st.val}
                  onClick={() => setStatusFilter(st.val)}
                  className="flex items-center gap-2 text-xs font-medium w-full text-left"
                >
                  {isSelected ? (
                    <CheckSquare size={13} className="text-teal-500" />
                  ) : (
                    <Square size={13} className="text-zinc-650" />
                  )}
                  <span className={isSelected ? "text-zinc-300" : "text-zinc-500"}>{st.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Product Type section */}
        <div className="space-y-3 pt-4 border-t border-zinc-850/50">
          <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Product Type</div>
          <div className="space-y-2">
            {[
              { val: "ALL", label: "All Types" },
              { val: "PRODUCT", label: "Product" },
              { val: "BUNDLE", label: "Bundle" },
              { val: "SERVICE", label: "Service" }
            ].map((tp) => {
              const isSelected = productTypeFilter === tp.val;
              return (
                <button
                  key={tp.val}
                  onClick={() => setProductTypeFilter(tp.val)}
                  className="flex items-center gap-2 text-xs font-medium w-full text-left"
                >
                  {isSelected ? (
                    <CheckSquare size={13} className="text-teal-500" />
                  ) : (
                    <Square size={13} className="text-zinc-650" />
                  )}
                  <span className={isSelected ? "text-zinc-300" : "text-zinc-500"}>{tp.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Price Book section */}
        <div className="space-y-3 pt-4 border-t border-zinc-850/50">
          <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Price Book</div>
          <select
            value={selectedPriceBookId}
            onChange={(e) => setSelectedPriceBookId(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-850 text-zinc-400 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
          >
            <option value="ALL">All Price Books</option>
            {priceBooks.map((pb) => (
              <option key={pb.id} value={pb.id.toString()}>{pb.name}</option>
            ))}
          </select>
        </div>

        {/* Clear Filters */}
        <button
          onClick={() => {
            setSelectedCategories([]);
            setStatusFilter("ACTIVE");
            setProductTypeFilter("ALL");
            setSelectedPriceBookId("ALL");
            setSearchQuery("");
          }}
          className="w-full py-2 border border-zinc-850 hover:bg-zinc-900 rounded-lg text-[10px] font-extrabold uppercase text-zinc-400 hover:text-zinc-200 transition-colors flex items-center justify-center gap-1"
        >
          <RotateCcw size={10} />
          <span>Clear Filters</span>
        </button>

      </div>

      {/* ─── MAIN CONTENT: PRODUCT LISTINGS ─── */}
      <div className={`flex-1 space-y-6 transition-all duration-300 ${selectedProductId ? "max-w-[48%]" : "max-w-full"}`}>
        
        {/* Header Toolbar */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-1 flex items-center gap-2">
              <BookOpen size={28} className="text-zinc-500" />
              <span>Product Catalog</span>
            </h1>
            <p className="text-xs text-zinc-400">Browse through active product lines, classifications, and custom Price Books.</p>
          </div>

          <div className="flex items-center gap-2">
            {canImport && (
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setImportResult(null);
                  setIsImportModalOpen(true);
                }}
                className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 px-3.5 py-2 rounded-lg text-xs font-semibold hover:bg-zinc-800 hover:text-zinc-150 transition-colors"
                title="Import Excel catalog spreadsheet"
              >
                <Upload size={14} />
                <span>Import</span>
              </button>
            )}
            {canCreate && (
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center gap-1.5 bg-teal-500 text-zinc-950 px-4 py-2 rounded-lg text-xs font-extrabold hover:bg-teal-400 transition-colors shadow-lg shadow-teal-500/10"
              >
                <Plus size={14} />
                <span>New Product</span>
              </button>
            )}
          </div>
        </div>

        {/* Toolbar Search / View toggles */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-zinc-900 border border-zinc-850 p-2.5 rounded-xl shadow-md">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={16} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search items by name, SKU, category, or CRM product code..."
              className="w-full pl-9 pr-4 py-1.5 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-zinc-700 placeholder-zinc-650"
            />
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto self-end sm:self-auto justify-end">
            <div className="flex items-center gap-1 border-r border-zinc-800 pr-2.5">
              <span className="text-[10px] text-zinc-550 font-semibold whitespace-nowrap">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-transparent text-zinc-350 text-xs font-bold focus:outline-none cursor-pointer"
              >
                <option value="created_newest">Created On (Newest)</option>
                <option value="created_oldest">Created On (Oldest)</option>
                <option value="sku_asc">SKU (A-Z)</option>
                <option value="sku_desc">SKU (Z-A)</option>
                <option value="price_asc">Price (Low to High)</option>
                <option value="price_desc">Price (High to Low)</option>
              </select>
            </div>

            <div className="flex items-center bg-zinc-950 p-0.5 rounded-lg border border-zinc-800">
              <button
                onClick={() => setViewMode("list")}
                className={`p-1 rounded ${viewMode === "list" ? "bg-zinc-800 text-zinc-200" : "text-zinc-600 hover:text-zinc-400"}`}
              >
                <ListIcon size={14} />
              </button>
              <button
                onClick={() => setViewMode("grid")}
                className={`p-1 rounded ${viewMode === "grid" ? "bg-zinc-800 text-zinc-200" : "text-zinc-600 hover:text-zinc-400"}`}
              >
                <Grid size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* Showing density */}
        <div className="text-[10px] text-zinc-550 font-semibold pl-1.5 flex justify-between items-center">
          <span>Showing {processedProducts.length > 0 ? (page - 1) * pageSize + 1 : 0} to {Math.min(page * pageSize, processedProducts.length)} of {processedProducts.length} items</span>
          {statusFilter !== "ACTIVE" && <span className="text-amber-500 font-bold">Filters Active</span>}
        </div>

        {/* Main listing view */}
        {isLoading ? (
          <div className="border border-zinc-850 rounded-xl bg-zinc-900/30 p-24 text-center">
            <RefreshCw className="mx-auto text-teal-500 animate-spin mb-3" size={24} />
            <span className="text-sm text-zinc-400 font-medium">Fetching catalog items...</span>
          </div>
        ) : isError ? (
          <div className="border border-red-900/30 rounded-xl bg-red-950/10 p-12 text-center">
            <p className="text-sm text-red-400 font-semibold mb-2">Error loading product catalog</p>
            <p className="text-xs text-red-500">{(error as any)?.detail || "Unable to retrieve records."}</p>
          </div>
        ) : processedProducts.length === 0 ? (
          <div className="border border-zinc-850 rounded-xl bg-zinc-900/30 p-20 text-center">
            <BookOpen size={40} className="mx-auto text-zinc-650 mb-3" />
            <h3 className="text-sm font-bold text-zinc-200 mb-1">Catalog empty</h3>
            <p className="text-xs text-zinc-500 max-w-xs mx-auto mb-4">
              Add new catalog products or clear active filters to discover items.
            </p>
            {canCreate && (
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="inline-flex items-center gap-1.5 bg-zinc-800 border border-zinc-750 text-zinc-200 px-3.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-zinc-750 hover:text-zinc-100 transition-colors"
              >
                <Plus size={12} />
                <span>Create Product</span>
              </button>
            )}
          </div>
        ) : viewMode === "list" ? (
          
          /* TABLE VIEW */
          <div className="border border-zinc-850 rounded-xl bg-zinc-900/35 overflow-hidden shadow-lg">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 text-[10px] uppercase font-bold text-zinc-500 bg-zinc-900/50">
                    <th className="px-4.5 py-3">Product</th>
                    <th className="px-4 py-3">SKU</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Product Type</th>
                    <th className="px-4 py-3">Status</th>
                    {canViewCost && <th className="px-4 py-3">Cost</th>}
                    <th className="px-4 py-3">Base Price</th>
                    {canViewMargin && <th className="px-4 py-3">Margin</th>}
                    <th className="px-4 py-3 w-[60px]"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-850 text-xs">
                  {processedProducts.map((p) => {
                    const typeInfo = getProductTypeInfo(p.sku);
                    
                    const costPriceNum = p.cost_price !== undefined && p.cost_price !== null ? (typeof p.cost_price === "string" ? parseFloat(p.cost_price) : p.cost_price) : null;
                    const marginPercentageNum = p.margin_percentage !== undefined && p.margin_percentage !== null ? (typeof p.margin_percentage === "string" ? parseFloat(p.margin_percentage) : p.margin_percentage) : null;
                    const marginAmountNum = p.margin_amount !== undefined && p.margin_amount !== null ? (typeof p.margin_amount === "string" ? parseFloat(p.margin_amount) : p.margin_amount) : null;

                    return (
                      <tr
                        key={p.id}
                        onClick={() => {
                          setSelectedProductId(p.id);
                          setActiveTab("overview");
                        }}
                        className={`hover:bg-zinc-800/40 cursor-pointer transition-colors ${selectedProductId === p.id ? "bg-zinc-800/50" : ""} ${!p.is_active ? "opacity-60 bg-zinc-950/25" : ""}`}
                      >
                        <td className="px-4.5 py-3.5 flex items-start gap-2.5">
                          <div className="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700/60 flex items-center justify-center font-bold text-zinc-400 shrink-0 mt-0.5">
                            {getProductIcon(p.sku)}
                          </div>
                          <div>
                            <div className="font-semibold text-zinc-200">{p.name}</div>
                            <div className="text-[10px] text-zinc-550 max-w-[200px] truncate">{p.description || "No description provided."}</div>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-semibold text-zinc-450 tracking-wider font-mono text-[10px]">{p.sku}</td>
                        <td className="px-4 py-3 text-zinc-400 font-semibold">{p.category?.name || "Unclassified"}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase tracking-wide ${typeInfo.colorClass}`}>
                            {typeInfo.label}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold uppercase tracking-wide border ${
                            p.is_active 
                              ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/40" 
                              : "bg-zinc-800 text-zinc-455 border-zinc-750"
                          }`}>
                            {p.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        {canViewCost && (
                          <td className="px-4 py-3 text-zinc-450">
                            {costPriceNum !== null ? (
                              <span>${costPriceNum.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                            ) : (
                              <span>—</span>
                            )}
                          </td>
                        )}
                        <td className="px-4 py-3 text-zinc-300 font-extrabold">${p.base_price.toLocaleString("en-US", { minimumFractionDigits: 2 })}</td>
                        {canViewMargin && (
                          <td className="px-4 py-3 font-extrabold">
                            {marginPercentageNum !== null ? (
                              <div className="flex flex-col">
                                <span className={marginPercentageNum < 0 ? "text-red-400" : "text-teal-400"}>
                                  {marginPercentageNum.toFixed(2)}%
                                </span>
                                {marginAmountNum !== null && (
                                  <span className="text-[10px] text-zinc-550 font-medium">
                                    {marginAmountNum < 0 ? "-" : ""}${Math.abs(marginAmountNum).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span className="text-zinc-650 italic font-medium">N/A</span>
                            )}
                          </td>
                        )}
                        <td className="px-4 py-3 relative">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveMenuId(activeMenuId === p.id ? null : p.id);
                            }}
                            className="p-1 hover:bg-zinc-800 rounded-lg text-zinc-400 hover:text-zinc-200 transition-colors"
                          >
                            <MoreHorizontal size={16} />
                          </button>
                          
                          {/* Row Context Menu */}
                          {activeMenuId === p.id && (
                            <div 
                              onClick={(e) => e.stopPropagation()}
                              className="absolute right-4 mt-1.5 w-36 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl z-20 overflow-hidden divide-y divide-zinc-800"
                            >
                              <div className="py-1">
                                <button
                                  onClick={() => {
                                    setSelectedProductId(p.id);
                                    setActiveTab("overview");
                                    setActiveMenuId(null);
                                  }}
                                  className="flex items-center gap-2 w-full px-3 py-2 text-left text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                                >
                                  <Eye size={12} />
                                  <span>View Card</span>
                                </button>
                                {canUpdate && (
                                  <button
                                    onClick={() => {
                                      setSelectedProductId(p.id);
                                      setIsEditModalOpen(true);
                                      setActiveMenuId(null);
                                    }}
                                    className="flex items-center gap-2 w-full px-3 py-2 text-left text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                                  >
                                    <Edit2 size={12} />
                                    <span>Edit Product</span>
                                  </button>
                                )}
                              </div>
                              {isManager && (
                                <div className="py-1">
                                  {p.is_active ? (
                                    <button
                                      onClick={() => {
                                        setArchiveConfirmId(p.id);
                                        setActiveMenuId(null);
                                      }}
                                      className="flex items-center gap-2 w-full px-3 py-2 text-left text-zinc-450 hover:bg-zinc-800 hover:text-red-400 transition-colors"
                                    >
                                      <Archive size={12} />
                                      <span>Deactivate</span>
                                    </button>
                                  ) : (
                                    <button
                                      onClick={() => {
                                        setRestoreConfirmId(p.id);
                                        setActiveMenuId(null);
                                      }}
                                      className="flex items-center gap-2 w-full px-3 py-2 text-left text-teal-455 hover:bg-zinc-800 hover:text-teal-350 transition-colors"
                                    >
                                      <RotateCcw size={12} />
                                      <span>Restore</span>
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="border-t border-zinc-850 p-4 flex items-center justify-between text-xs text-zinc-500 bg-zinc-900/20">
              <div>
                Showing <span className="font-semibold text-zinc-400">{(page - 1) * pageSize + 1}</span> to{" "}
                <span className="font-semibold text-zinc-400">{Math.min(page * pageSize, processedProducts.length)}</span>{" "}
                of <span className="font-semibold text-zinc-400">{processedProducts.length}</span> items
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft size={14} />
                </button>
                <span className="px-3 text-zinc-300 font-medium">Page {page}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page * pageSize >= processedProducts.length}
                  className="p-1.5 rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        ) : (
          
          /* GRID VIEW */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {processedProducts.map((p) => {
              const typeInfo = getProductTypeInfo(p.sku);
              return (
                <div
                  key={p.id}
                  onClick={() => setSelectedProductId(p.id)}
                  className={`bg-zinc-900/35 border border-zinc-850 rounded-xl p-4.5 space-y-4 hover:border-zinc-700 cursor-pointer transition-all relative ${selectedProductId === p.id ? "border-teal-500/80 bg-zinc-900/60" : ""} ${!p.is_active ? "opacity-60 bg-zinc-950/25" : ""}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex gap-2.5 items-start">
                      <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center font-bold">
                        {getProductIcon(p.sku)}
                      </div>
                      <div>
                        <h4 className="font-bold text-zinc-200 text-xs">{p.name}</h4>
                        <span className="text-[10px] text-zinc-550 font-mono tracking-wide">{p.sku}</span>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[8px] font-extrabold uppercase border ${
                      p.is_active ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/40" : "bg-zinc-800 text-zinc-450 border-zinc-750"
                    }`}>
                      {p.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>

                  <p className="text-[10px] text-zinc-500 leading-normal line-clamp-2 h-7">{p.description || "No description provided."}</p>

                  <div className="flex justify-between items-center pt-2.5 border-t border-zinc-850">
                    <span className="text-xs text-zinc-400 font-medium">{p.category?.name || "Unclassified"}</span>
                    <span className="text-sm font-extrabold text-zinc-150">${p.base_price.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ─── RIGHT PANEL: SELECTED PRODUCT DETAILS ─── */}
      {selectedProductId && selectedProduct && (
        <div className="w-[33%] bg-zinc-900/60 border border-zinc-850 rounded-2xl shadow-xl flex flex-col fixed top-32 right-8 bottom-8 z-10 overflow-hidden animate-in slide-in-from-right duration-250 backdrop-blur-xl">
          
          {/* Detail Header */}
          <div className="p-4 border-b border-zinc-850 flex items-center justify-between bg-zinc-900/80">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${selectedProduct.is_active ? "bg-emerald-400 animate-pulse" : "bg-zinc-650"}`} />
              <h2 className="font-bold text-zinc-100 truncate max-w-[150px]">{selectedProduct.name}</h2>
            </div>
            <div className="flex items-center gap-1">
              {isManager && (
                selectedProduct.is_active ? (
                  <button
                    onClick={() => setArchiveConfirmId(selectedProduct.id)}
                    className="p-1 text-zinc-400 hover:text-red-400 hover:bg-zinc-800 rounded transition-colors"
                    title="Deactivate item"
                  >
                    <Archive size={14} />
                  </button>
                ) : (
                  <button
                    onClick={() => setRestoreConfirmId(selectedProduct.id)}
                    className="p-1 text-zinc-400 hover:text-teal-400 hover:bg-zinc-800 rounded transition-colors"
                    title="Restore item"
                  >
                    <RotateCcw size={14} />
                  </button>
                )
              )}
              <button
                onClick={() => setSelectedProductId(null)}
                className="p-1 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-850 rounded-lg transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Details Tabs */}
          <div className="flex border-b border-zinc-850 bg-zinc-900/40 text-[11px] font-semibold text-zinc-400 font-sans">
            {(["overview", "pricing"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-3 text-center border-b-2 capitalize transition-colors ${
                  activeTab === tab
                    ? "border-teal-400 text-teal-400 bg-zinc-850/20"
                    : "border-transparent hover:text-zinc-200"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Details Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-6 text-xs">
            
            {/* OVERVIEW TAB */}
            {activeTab === "overview" && (
              <div className="space-y-6">
                
                {/* Product Info Card */}
                <div className="space-y-4 bg-zinc-900/45 p-4 rounded-xl border border-zinc-850">
                  <div className="flex justify-between items-center pb-2 border-b border-zinc-800">
                    <h3 className="font-bold text-zinc-350">General Specifications</h3>
                    {canUpdate && selectedProduct.is_active && (
                      <button
                        onClick={() => setIsEditModalOpen(true)}
                        className="p-1 text-zinc-500 hover:text-teal-400 rounded transition-colors"
                      >
                        <Edit2 size={12} />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-y-3.5 gap-x-2">
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Product SKU</div>
                      <div className="text-zinc-300 font-mono font-semibold tracking-wide">{selectedProduct.sku}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Category</div>
                      <div className="text-zinc-300 font-medium">{selectedProduct.category?.name || "Unclassified"}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">CRM Product Code</div>
                      <div className="text-zinc-300 font-mono truncate">{selectedProduct.external_crm_id || "Not synced"}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-550 font-semibold mb-0.5">Catalog Status</div>
                      <div>
                        <span className={`px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase border ${
                          selectedProduct.is_active ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/40" : "bg-zinc-850 text-zinc-455 border-zinc-750"
                        }`}>
                          {selectedProduct.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Description Card */}
                <div className="space-y-3 bg-zinc-900/45 p-4 rounded-xl border border-zinc-850">
                  <h3 className="font-bold text-zinc-350 pb-2 border-b border-zinc-800">Marketing Description</h3>
                  <p className="text-zinc-450 leading-relaxed font-medium">{selectedProduct.description || "No description provided for this product SKU."}</p>
                </div>

              </div>
            )}

            {/* PRICING TAB */}
            {activeTab === "pricing" && (
              <div className="space-y-6">
                
                {/* Base List Price Card */}
                <div className="bg-zinc-900/45 p-4 rounded-xl border border-zinc-850 space-y-3.5">
                  <h3 className="font-bold text-zinc-350 pb-2 border-b border-zinc-800">Standard Pricing</h3>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between items-center bg-zinc-950 border border-zinc-850 p-3 rounded-lg">
                      <div>
                        <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Base Unit Price</div>
                        <div className="text-[10px] text-zinc-600">Standard selling list price</div>
                      </div>
                      <div className="text-base font-black text-zinc-250">
                        ${selectedProduct.base_price.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </div>
                    </div>

                    <div className="flex justify-between items-center bg-zinc-950 border border-zinc-850 p-3 rounded-lg">
                      <div>
                        <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Billing Type</div>
                        <div className="text-[10px] text-zinc-600">Product charge model</div>
                      </div>
                      <div className="text-xs font-bold text-zinc-300 bg-zinc-900 px-2 py-1 rounded border border-zinc-805 uppercase font-mono">
                        {selectedProduct.billing_type === "MRC" ? "MRC (Recurring)" : selectedProduct.billing_type === "NRC" ? "NRC (One-time)" : "Usage (Consump.)"}
                      </div>
                    </div>

                    {canViewCost && (
                      <div className="flex justify-between items-center bg-zinc-950 border border-zinc-850 p-3 rounded-lg">
                        <div>
                          <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Product Cost</div>
                          <div className="text-[10px] text-zinc-600">Sensitive manufacturing cost</div>
                        </div>
                        <div className="text-base font-black text-zinc-350">
                          {selCostNum !== null ? (
                            <span>${selCostNum.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                          ) : (
                            "—"
                          )}
                        </div>
                      </div>
                    )}

                    {canViewMargin && (
                      <div className="flex justify-between items-center bg-zinc-950 border border-zinc-850 p-3 rounded-lg">
                        <div>
                          <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Gross Margin</div>
                          <div className="text-[10px] text-zinc-600">Computed gross profit</div>
                        </div>
                        <div className="text-right">
                          <div className={`text-base font-black ${
                            selMarginPercentNum !== null && selMarginPercentNum < 0 
                              ? "text-red-400" 
                              : "text-teal-400"
                          }`}>
                            {selMarginPercentNum !== null ? (
                              `${selMarginPercentNum.toFixed(2)}%`
                            ) : (
                              "N/A"
                            )}
                          </div>
                          {selMarginAmtNum !== null && (
                            <div className="text-[10px] text-zinc-550 font-bold">
                              {selMarginAmtNum < 0 ? "-" : ""}${Math.abs(selMarginAmtNum).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Price Book Custom Entries */}
                <div className="bg-zinc-900/45 p-4 rounded-xl border border-zinc-850 space-y-4">
                  <h3 className="font-bold text-zinc-350 pb-2 border-b border-zinc-800">Price Book Custom Mappings</h3>
                  
                  <div className="space-y-2.5">
                    {priceBooks.length > 0 ? (
                      priceBooks.map((pb) => {
                        const customEntry = pb.entries?.find((e) => e.product_id === selectedProduct.id);
                        return (
                          <div key={pb.id} className="flex justify-between items-center p-2.5 bg-zinc-950/70 border border-zinc-850/60 rounded-lg">
                            <div>
                              <div className="font-bold text-zinc-350">{pb.name}</div>
                              <span className="text-[9px] text-zinc-555 font-bold uppercase tracking-wider">{pb.is_standard ? "Standard Price Book" : "Custom Catalog"}</span>
                            </div>
                            <div className="text-zinc-200 font-black">
                              {customEntry ? (
                                `$${customEntry.custom_price.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                              ) : (
                                <span className="text-zinc-600 font-semibold italic text-[11px]">Inherit Base List</span>
                              )}
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-center py-6 text-zinc-650 font-medium">No active price books found.</div>
                    )}
                  </div>
                </div>

              </div>
            )}

          </div>
        </div>
      )}

      {/* ─── MODAL: CREATE CATALOG PRODUCT ─── */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-zinc-850">
              <h2 className="text-base font-bold text-zinc-100 flex items-center gap-1.5">
                <Plus className="text-teal-400" size={18} />
                <span>Onboard New Catalog SKU</span>
              </h2>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="p-1 text-zinc-550 hover:text-zinc-150 hover:bg-zinc-800 rounded transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateProductSubmit} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Product SKU *</label>
                  <input
                    type="text"
                    name="sku"
                    required
                    placeholder="e.g. LAP-DL7440"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-zinc-750 font-mono text-[11px]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Marketing Name *</label>
                  <input
                    type="text"
                    name="name"
                    required
                    placeholder="e.g. Dell Latitude 7440"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-bold text-zinc-400">Marketing Description</label>
                <textarea
                  name="description"
                  placeholder="Summarize product specifications..."
                  className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none min-h-[60px]"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Base Price *</label>
                  <input
                    type="number"
                    name="base_price"
                    step="0.01"
                    min="0"
                    required
                    placeholder="1299.00"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Product Cost</label>
                  <input
                    type="number"
                    name="cost_price"
                    step="0.01"
                    min="0"
                    disabled={!canManageCost}
                    placeholder={canManageCost ? "800.00" : "Hidden"}
                    className={`w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none ${!canManageCost ? "cursor-not-allowed opacity-50" : ""}`}
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Billing Type *</label>
                  <select
                    name="billing_type"
                    required
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  >
                    <option value="MRC">Monthly Recurring (MRC)</option>
                    <option value="NRC">Non-Recurring (NRC)</option>
                    <option value="USAGE">Usage-Based (Usage)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Category Taxonomy</label>
                  <select
                    name="category_id"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  >
                    <option value="">No Category</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">CRM Product Code</label>
                  <input
                    type="text"
                    name="external_crm_id"
                    placeholder="e.g. 01t5G..."
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none font-mono text-[11px]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Initial Status</label>
                  <select
                    name="is_active"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  >
                    <option value="true">Active (Publish immediately)</option>
                    <option value="false">Inactive (Draft)</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-zinc-850">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-semibold hover:bg-zinc-750"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-teal-500 text-zinc-950 px-5 py-2 rounded-lg font-bold hover:bg-teal-400"
                >
                  Onboard SKU
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: EDIT CATALOG PRODUCT ─── */}
      {isEditModalOpen && selectedProduct && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-zinc-850">
              <h2 className="text-base font-bold text-zinc-100 flex items-center gap-1.5">
                <Edit2 className="text-zinc-500" size={16} />
                <span>Modify Catalog SKU</span>
              </h2>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="p-1 text-zinc-550 hover:text-zinc-150 hover:bg-zinc-800 rounded transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleEditProductSubmit} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Product SKU *</label>
                  <input
                    type="text"
                    name="sku"
                    defaultValue={selectedProduct.sku}
                    required
                    placeholder="e.g. LAP-DL7440"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none font-mono text-[11px]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Marketing Name *</label>
                  <input
                    type="text"
                    name="name"
                    defaultValue={selectedProduct.name}
                    required
                    placeholder="e.g. Dell Latitude 7440"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-bold text-zinc-400">Marketing Description</label>
                <textarea
                  name="description"
                  defaultValue={selectedProduct.description || ""}
                  placeholder="Summarize product specifications..."
                  className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none min-h-[60px]"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Base Price *</label>
                  <input
                    type="number"
                    name="base_price"
                    step="0.01"
                    min="0"
                    defaultValue={selectedProduct.base_price}
                    required
                    placeholder="1299.00"
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Product Cost</label>
                  <input
                    type="number"
                    name="cost_price"
                    step="0.01"
                    min="0"
                    defaultValue={selectedProduct.cost_price ?? ""}
                    disabled={!canManageCost}
                    placeholder={canManageCost ? "800.00" : "Hidden"}
                    className={`w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none ${!canManageCost ? "cursor-not-allowed opacity-50" : ""}`}
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Billing Type *</label>
                  <select
                    name="billing_type"
                    defaultValue={selectedProduct.billing_type}
                    required
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  >
                    <option value="MRC">Monthly Recurring (MRC)</option>
                    <option value="NRC">Non-Recurring (NRC)</option>
                    <option value="USAGE">Usage-Based (Usage)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Category Taxonomy</label>
                  <select
                    name="category_id"
                    defaultValue={selectedProduct.category_id || ""}
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  >
                    <option value="">No Category</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">CRM Product Code</label>
                  <input
                    type="text"
                    name="external_crm_id"
                    defaultValue={selectedProduct.external_crm_id ?? ""}
                    placeholder="e.g. 01t5G..."
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none font-mono text-[11px]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-zinc-400">Initial Status</label>
                  <select
                    name="is_active"
                    defaultValue={selectedProduct.is_active ? "true" : "false"}
                    className="w-full p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none"
                  >
                    <option value="true">Active (Publish)</option>
                    <option value="false">Inactive (Draft/Archived)</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-zinc-850">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-semibold hover:bg-zinc-750"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-teal-500 text-zinc-955 px-5 py-2 rounded-lg font-bold hover:bg-teal-400"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: EXCEL PRODUCT IMPORT ─── */}
      {isImportModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4 overflow-hidden max-h-[85vh] flex flex-col">
            
            <div className="flex justify-between items-center pb-2 border-b border-zinc-850 shrink-0">
              <h2 className="text-base font-bold text-zinc-100 flex items-center gap-1.5">
                <Upload className="text-teal-400" size={18} />
                <span>Import Products</span>
              </h2>
              <button
                onClick={() => setIsImportModalOpen(false)}
                className="p-1 text-zinc-550 hover:text-zinc-150 hover:bg-zinc-800 rounded transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Main Area */}
            <div className="flex-1 overflow-y-auto pr-1 space-y-4">
              
              {!importResult ? (
                // File Selection Form
                <div className="space-y-4 text-xs">
                  <div className="border-2 border-dashed border-zinc-800 hover:border-zinc-700 bg-zinc-950 p-6 rounded-xl text-center cursor-pointer transition-colors relative">
                    <input
                      type="file"
                      accept=".xlsx, .xls"
                      onChange={handleFileChange}
                      className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                    />
                    <Upload size={24} className="mx-auto text-zinc-500 mb-2" />
                    <div className="text-zinc-300 font-bold">Select Catalog Excel File</div>
                    <p className="text-[10px] text-zinc-600 mt-1">Accepts .xlsx or .xls spreadsheets only</p>
                  </div>

                  {selectedFile && (
                    <div className="bg-zinc-950 border border-zinc-850 p-3 rounded-lg flex items-center justify-between">
                      <div>
                        <div className="font-bold text-zinc-250">{selectedFile.name}</div>
                        <div className="text-[10px] text-zinc-550 mt-0.5">Size: {(selectedFile.size / 1024).toFixed(1)} KB</div>
                      </div>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="text-zinc-500 hover:text-zinc-300"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  )}

                  {importProductsMutation.isPending && (
                    <div className="flex items-center justify-center gap-2 py-4 text-teal-400 font-bold">
                      <RefreshCw className="animate-spin" size={16} />
                      <span>Uploading and parsing spreadsheet...</span>
                    </div>
                  )}

                  {importProductsMutation.isError && (
                    <div className="bg-red-955/20 border border-red-900/40 p-3 rounded-lg text-red-400 flex items-start gap-2">
                      <AlertCircle className="shrink-0 mt-0.5" size={14} />
                      <div>
                        <div className="font-bold">Upload Failed</div>
                        <div className="text-[10px] mt-0.5">{(importProductsMutation.error as any)?.detail || "Check spreadsheet column structure and file format."}</div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                // Import Results View
                <div className="space-y-4 text-xs">
                  <div className="bg-zinc-950 border border-zinc-850 p-4 rounded-xl space-y-3.5">
                    <h3 className="font-bold text-zinc-250 text-sm">Import Summary</h3>
                    
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="bg-zinc-900 p-2.5 rounded border border-zinc-800">
                        <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Total Rows</div>
                        <div className="text-lg font-black text-zinc-200 mt-1">{importResult.total_rows}</div>
                      </div>
                      <div className="bg-zinc-900 p-2.5 rounded border border-zinc-800">
                        <div className="text-[10px] text-teal-500 font-bold uppercase tracking-wider">Imported</div>
                        <div className="text-lg font-black text-teal-400 mt-1">{importResult.imported_count}</div>
                      </div>
                      <div className="bg-zinc-900 p-2.5 rounded border border-zinc-800">
                        <div className="text-[10px] text-red-500 font-bold uppercase tracking-wider">Failed</div>
                        <div className="text-lg font-black text-red-400 mt-1">{importResult.failed_count}</div>
                      </div>
                    </div>
                  </div>

                  {importResult.errors.length > 0 && (
                    <div className="space-y-2 shrink-0">
                      <h4 className="font-bold text-zinc-350 pl-0.5">Validation Errors ({importResult.errors.length})</h4>
                      <div className="border border-zinc-850 rounded-lg overflow-hidden max-h-[180px] overflow-y-auto">
                        <table className="w-full text-left text-[11px]">
                          <thead>
                            <tr className="bg-zinc-950 text-zinc-550 border-b border-zinc-850 font-bold uppercase tracking-wider text-[9px]">
                              <th className="px-3 py-1.5 w-[50px] text-center">Row</th>
                              <th className="px-3 py-1.5 w-[120px]">SKU</th>
                              <th className="px-3 py-1.5">Error</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-zinc-850 bg-zinc-900/40 text-zinc-400 font-medium">
                            {importResult.errors.map((err, i) => (
                              <tr key={i} className="hover:bg-zinc-900/30">
                                <td className="px-3 py-1.5 text-center text-zinc-500">{err.row}</td>
                                <td className="px-3 py-1.5 font-mono text-[10px]">{err.sku || "—"}</td>
                                <td className="px-3 py-1.5 text-red-400">{err.error}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer buttons */}
            <div className="flex justify-end gap-2.5 pt-4 border-t border-zinc-850 shrink-0">
              {!importResult ? (
                <>
                  <button
                    type="button"
                    onClick={() => setIsImportModalOpen(false)}
                    className="bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-semibold hover:bg-zinc-750 text-xs"
                    disabled={importProductsMutation.isPending}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={triggerUpload}
                    className="bg-teal-500 text-zinc-955 px-5 py-2 rounded-lg font-bold hover:bg-teal-400 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={!selectedFile || importProductsMutation.isPending}
                  >
                    Upload File
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setIsImportModalOpen(false);
                    setImportResult(null);
                    setSelectedFile(null);
                  }}
                  className="bg-teal-500 text-zinc-955 px-5 py-2 rounded-lg font-bold hover:bg-teal-400 text-xs"
                >
                  Close Results
                </button>
              )}
            </div>

          </div>
        </div>
      )}

      {/* ─── CONFIRMATION MODAL: DEACTIVATE PRODUCT ─── */}
      {archiveConfirmId !== null && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-sm p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-zinc-100">Deactivate Catalog SKU?</h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Deactivating this SKU prevents it from being added to new configuration blueprints and quotes. Existing quote history reference configurations will remain intact.
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
                onClick={() => archiveProductMutation.mutate(archiveConfirmId)}
                className="bg-red-500 text-zinc-950 px-5 py-2 rounded-lg font-bold hover:bg-red-400 text-xs transition-colors"
              >
                Deactivate Product
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── CONFIRMATION MODAL: RESTORE PRODUCT ─── */}
      {restoreConfirmId !== null && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-850 rounded-2xl w-full max-w-sm p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-zinc-100">Restore Catalog SKU?</h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Restoring this SKU will republish it immediately in the active product catalogs, making it available for config building and quoting calculations.
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
                onClick={() => restoreProductMutation.mutate(restoreConfirmId)}
                className="bg-teal-500 text-zinc-955 px-5 py-2 rounded-lg font-bold hover:bg-teal-400 text-xs transition-colors"
              >
                Restore Product
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
