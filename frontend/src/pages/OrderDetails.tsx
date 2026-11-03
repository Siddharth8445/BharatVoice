
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft, Check, CircleAlert, Clock3, Loader2, Plus, Save,
  ShieldCheck, Trash2, Volume2, X,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  cancelOrder,
  confirmOrder,
  editOrder,
  getOrder,
  speakConfirmation,
} from '../api/orders';
import { OrderItemCreate, OrderResponse } from '../types/order';
import StatusBadge from '../components/ui/StatusBadge';

const errorMessage = (error: unknown) => {
  const value = error as {
    response?: { data?: { detail?: string } };
    message?: string;
  };

  return (
    value.response?.data?.detail ||
    value.message ||
    'Something went wrong. Please try again.'
  );
};

const formatINR = (amount: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(amount);

const toEditableItems = (order: OrderResponse): OrderItemCreate[] =>
  order.items.map((item) => ({
    product_name: item.product_name,
    product_id: item.product_id ?? null,
    quantity: item.quantity,
    unit: item.unit,
    unit_price: item.unit_price ?? null,
  }));

const OrderDetails: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const id = Number(orderId);

  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [items, setItems] = useState<OrderItemCreate[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [error, setError] = useState('');
  const [audioUrl, setAudioUrl] = useState('');

  const loadOrder = useCallback(async () => {
    if (!Number.isInteger(id) || id <= 0) {
      setError('This order ID is invalid.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await getOrder(id);
      setOrder(result);
      setItems(toEditableItems(result));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadOrder();
  }, [loadOrder]);

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  // Editing a product name clears the previous catalogue ID.
  // This prevents an old product ID from overriding the new name.
  const updateItem = (
    index: number,
    field: 'product_name' | 'quantity' | 'unit',
    value: string,
  ) => {
    setItems((current) =>
      current.map((item, itemIndex) => {
        if (index !== itemIndex) return item;

        if (field === 'quantity') {
          return {
            ...item,
            quantity: value === '' ? 0 : Number(value),
          };
        }

        if (field === 'product_name') {
          return {
            ...item,
            product_name: value,
            product_id: null,
          };
        }

        return { ...item, unit: value };
      }),
    );
  };

  const totals = useMemo(() => {
    const lineTotals = items.map((item) => {
      const quantity = Number(item.quantity) || 0;
      const unitPrice = Number(item.unit_price) || 0;
      return quantity * unitPrice;
    });

    return {
      lineTotals,
      grandTotal: lineTotals.reduce((sum, value) => sum + value, 0),
    };
  }, [items]);

  const saveItems = async () => {
    if (!items.length) {
      toast.error('Add at least one item before saving the order.');
      return;
    }

    if (
      items.some(
        (item) =>
          !item.product_name.trim() ||
          !item.unit.trim() ||
          !Number.isFinite(item.quantity) ||
          item.quantity <= 0,
      )
    ) {
      toast.error(
        'Every item needs a product name, positive quantity and unit.',
      );
      return;
    }

    setSaving(true);

    try {
      const updated = await editOrder(id, items);
      setOrder(updated);
      setItems(toEditableItems(updated));
      setEditMode(false);

      if (updated.status === 'needs_clarification') {
        toast.error(
          updated.clarification_message ||
            'Some items still need clarification.',
        );
      } else if (updated.status === 'awaiting_confirmation') {
        toast.success('Order reviewed and ready for approval.');
      } else {
        toast.success('Order items saved.');
      }
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const confirm = async () => {
    if (
      !order ||
      order.status !== 'awaiting_confirmation' ||
      order.clarification_required ||
      order.items.length === 0
    ) {
      return;
    }

    if (
      !window.confirm(
        'Confirm this order? This records the shopkeeper’s approval.',
      )
    ) {
      return;
    }

    setActionBusy(true);

    try {
      const updated = await confirmOrder(id);
      setOrder(updated);
      toast.success('Order confirmed successfully.');
    } catch (err) {
      toast.error(errorMessage(err));
      await loadOrder();
    } finally {
      setActionBusy(false);
    }
  };

  const cancel = async () => {
    if (
      !order ||
      ![
        'awaiting_confirmation',
        'needs_clarification',
        'draft',
      ].includes(order.status)
    ) {
      return;
    }

    if (
      !window.confirm(
        'Cancel this unconfirmed order? This action cannot be undone.',
      )
    ) {
      return;
    }

    setActionBusy(true);

    try {
      const updated = await cancelOrder(id);
      setOrder(updated);
      toast.success('Order cancelled.');
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setActionBusy(false);
    }
  };

  const playConfirmation = async () => {
    setActionBusy(true);

    try {
      const blob = await speakConfirmation(id);

      if (audioUrl) URL.revokeObjectURL(audioUrl);

      setAudioUrl(URL.createObjectURL(blob));
      toast.success('Hindi confirmation audio generated.');
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setActionBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl animate-pulse space-y-4">
        <div className="h-8 w-48 rounded bg-slate-200" />
        <div className="h-40 rounded-2xl bg-slate-100" />
        <div className="h-64 rounded-2xl bg-slate-100" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800">
        <div className="flex items-center gap-2 font-semibold">
          <CircleAlert className="h-5 w-5" />
          Unable to load order
        </div>
        <p className="mt-2 text-sm">{error}</p>
        <div className="mt-4 flex gap-3">
          <button
            onClick={() => void loadOrder()}
            className="rounded-lg bg-red-700 px-4 py-2 text-sm font-semibold text-white"
          >
            Retry
          </button>
          <Link
            to="/orders"
            className="rounded-lg border border-red-300 px-4 py-2 text-sm font-semibold"
          >
            Back to orders
          </Link>
        </div>
      </div>
    );
  }

  if (!order) return null;

  const canEdit = [
    'draft',
    'pending',
    'awaiting_confirmation',
    'needs_clarification',
  ].includes(order.status);

  const canCancel = [
    'draft',
    'pending',
    'awaiting_confirmation',
    'needs_clarification',
  ].includes(order.status);

  const unresolved =
    order.status === 'needs_clarification' ||
    order.clarification_required;

  const canConfirm =
    order.status === 'awaiting_confirmation' &&
    !unresolved &&
    order.items.length > 0;

  return (
    <div className="mx-auto max-w-5xl space-y-6">

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link
            to="/orders"
            className="mb-3 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-blue-700"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to all orders
          </Link>

          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">
            Order workspace
          </p>

          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-slate-900">
            Order #{order.id}
          </h1>
        </div>

        <StatusBadge status={order.status} />
      </div>

      {/* Customer request */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-bold text-slate-900">Customer request</h2>
            <p className="mt-1 text-xs text-slate-500">
              Original speech-to-text transcript
            </p>
          </div>

          <div className="text-right text-xs text-slate-500">
            <p>Created {new Date(order.created_at).toLocaleString()}</p>
            <p className="mt-1">
              Updated {new Date(order.updated_at).toLocaleString()}
            </p>
          </div>
        </div>

        <blockquote className="mt-5 rounded-xl border-l-4 border-blue-500 bg-blue-50 px-5 py-4 text-sm leading-7 text-slate-800">
          {order.transcript || 'No transcript was saved for this order.'}
        </blockquote>
      </section>

      {/* Exact backend clarification */}
      {unresolved && (
        <div className="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-amber-900">
          <CircleAlert className="h-5 w-5 shrink-0" />

          <div>
            <p className="text-sm font-bold">
              Clarification required
            </p>

            <p className="mt-1 text-sm leading-6">
              {order.clarification_message ||
                'Review the extracted items and correct the missing or invalid information.'}
            </p>

            {order.unsupported_products?.length > 0 && (
              <p className="mt-2 text-xs font-semibold">
                Products requiring attention:{' '}
                {order.unsupported_products.join(', ')}
              </p>
            )}

            {canEdit && (
              <p className="mt-2 text-xs">
                Edit the items below and save your changes to revalidate this order.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Order items */}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 py-5">
          <div>
            <h2 className="font-bold text-slate-900">Order items</h2>
            <p className="mt-1 text-xs text-slate-500">
              {items.length} line item{items.length === 1 ? '' : 's'} · verify quantities and prices
            </p>
          </div>

          {canEdit && (
            <button
              onClick={() => {
                if (editMode) {
                  setItems(toEditableItems(order));
                  setEditMode(false);
                } else {
                  setItems(toEditableItems(order));
                  setEditMode(true);
                }
              }}
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              {editMode ? 'Discard changes' : 'Edit items'}
            </button>
          )}
        </div>

        {items.length === 0 && !editMode ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm font-semibold text-slate-800">
              No items extracted
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Add the items manually to resolve this order.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-6 py-3">Product</th>
                  <th className="px-6 py-3">Quantity</th>
                  <th className="px-6 py-3">Unit</th>
                  <th className="px-6 py-3 text-right">Unit price</th>
                  <th className="px-6 py-3 text-right">Subtotal</th>
                  {editMode && <th className="px-6 py-3" />}
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {items.map((item, index) => (
                  <tr key={`${item.product_id || item.product_name}-${index}`}>
                    <td className="px-6 py-3">
                      {editMode ? (
                        <input
                          aria-label="Product name"
                          value={item.product_name}
                          onChange={(event) =>
                            updateItem(index, 'product_name', event.target.value)
                          }
                          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                        />
                      ) : (
                        <span className="text-sm font-semibold text-slate-800">
                          {item.product_name}
                        </span>
                      )}
                    </td>

                    <td className="px-6 py-3">
                      {editMode ? (
                        <input
                          aria-label="Quantity"
                          type="number"
                          min="0.001"
                          step="0.001"
                          value={item.quantity}
                          onChange={(event) =>
                            updateItem(index, 'quantity', event.target.value)
                          }
                          className="w-24 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                        />
                      ) : (
                        <span className="text-sm text-slate-700">
                          {item.quantity}
                        </span>
                      )}
                    </td>

                    <td className="px-6 py-3">
                      {editMode ? (
                        <input
                          aria-label="Unit"
                          value={item.unit}
                          onChange={(event) =>
                            updateItem(index, 'unit', event.target.value)
                          }
                          className="w-24 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                        />
                      ) : (
                        <span className="text-sm text-slate-600">
                          {item.unit}
                        </span>
                      )}
                    </td>

                    <td className="px-6 py-3 text-right text-sm text-slate-600">
                      {formatINR(Number(item.unit_price) || 0)}
                    </td>

                    <td className="px-6 py-3 text-right text-sm font-semibold text-slate-900">
                      {formatINR(totals.lineTotals[index] || 0)}
                    </td>

                    {editMode && (
                      <td className="px-6 py-3 text-right">
                        <button
                          onClick={() =>
                            setItems((current) =>
                              current.filter((_, itemIndex) => itemIndex !== index),
                            )
                          }
                          aria-label="Remove item"
                          className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Total */}
        <div className="flex justify-end border-t border-slate-100 bg-slate-50 px-6 py-5">
          <div className="w-full max-w-xs space-y-2">
            <div className="flex justify-between text-sm text-slate-500">
              <span>Items</span>
              <span>{items.length}</span>
            </div>

            <div className="flex justify-between border-t border-slate-200 pt-3 text-base font-bold text-slate-900">
              <span>Estimated total</span>
              <span>{formatINR(totals.grandTotal)}</span>
            </div>

            <p className="text-right text-[11px] text-slate-400">
              Based on catalogue unit prices
            </p>
          </div>
        </div>

        {/* Edit actions */}
        {editMode && (
          <div className="flex flex-wrap gap-2 border-t border-slate-100 px-6 py-4">
            <button
              onClick={() =>
                setItems((current) => [
                  ...current,
                  {
                    product_name: '',
                    quantity: 1,
                    unit: 'kg',
                    product_id: null,
                    unit_price: null,
                  },
                ])
              }
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              <Plus className="h-4 w-4" />
              Add item
            </button>

            <button
              onClick={() => void saveItems()}
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save changes
            </button>

            <button
              onClick={() => {
                setItems(toEditableItems(order));
                setEditMode(false);
              }}
              className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-100"
            >
              Cancel
            </button>
          </div>
        )}
      </section>

      {/* Approval */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-50 p-3 text-blue-700">
            <ShieldCheck className="h-5 w-5" />
          </div>

          <div>
            <h2 className="font-bold text-slate-900">Order approval</h2>
            <p className="mt-1 text-xs text-slate-500">
              Only a shopkeeper action can confirm an order.
            </p>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          {canConfirm && (
            <button
              onClick={() => void confirm()}
              disabled={actionBusy || editMode}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              <Check className="h-4 w-4" />
              Confirm order
            </button>
          )}

          {canCancel && (
            <button
              onClick={() => void cancel()}
              disabled={actionBusy || editMode}
              className="inline-flex items-center gap-2 rounded-xl border border-rose-200 px-4 py-2.5 text-sm font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-50"
            >
              <X className="h-4 w-4" />
              Cancel order
            </button>
          )}

          {order.status === 'confirmed' && (
            <button
              onClick={() => void playConfirmation()}
              disabled={actionBusy}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              <Volume2 className="h-4 w-4" />
              Generate spoken confirmation
            </button>
          )}

          {order.status === 'confirmed' && (
            <span className="inline-flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-2.5 text-sm font-semibold text-emerald-700">
              <Check className="h-4 w-4" />
              Approved
            </span>
          )}

          {order.status === 'cancelled' && (
            <span className="rounded-xl bg-rose-50 px-4 py-2.5 text-sm font-semibold text-rose-700">
              This order was cancelled.
            </span>
          )}
        </div>

        {unresolved && (
          <p className="mt-3 flex items-center gap-2 text-xs text-amber-700">
            <Clock3 className="h-4 w-4" />
            Resolve the clarification and save the order before approval.
          </p>
        )}

        {audioUrl && (
          <div className="mt-5 rounded-xl bg-slate-50 p-4">
            <p className="mb-2 text-xs font-semibold text-slate-600">
              Spoken confirmation audio
            </p>
            <audio controls src={audioUrl} className="w-full" />
          </div>
        )}
      </section>
    </div>
  );
};

export default OrderDetails;
