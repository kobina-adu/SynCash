// app/request/page.tsx
"use client";

import { useState } from "react";
import { Wallet, Users } from "lucide-react";

export default function RequestMoneyPage() {
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);
  const [form, setForm] = useState({
    phone: '',
    name: '',
    amount: '',
    message: ''
  });
  const [errors, setErrors] = useState<any>({});
  const [success, setSuccess] = useState(false);

const wallets = [
{ id: "mtn", name: "MTN MoMo", balance: "₵8,500.00", color: "bg-yellow-400" },
{ id: "telecel", name: "Telecel Cash", balance: "₵4,200.00", color: "bg-red-500" },
{ id: "airtel", name: "AirtelTigo", balance: "₵1,847.50", color: "bg-green-500" },
{ id: "gcb", name: "GCB Bank", balance: "₵1,300.00", color: "bg-blue-500" },
];

const recentContacts = [
{ initials: "AO", name: "Ama Osei", phone: "0244123456" },
{ initials: "KM", name: "Kofi Mensah", phone: "0209876543" },
{ initials: "AF", name: "Akosua", phone: "0551122334" },
{ initials: "KA", name: "Kwaku Asante", phone: "0554567890" },
];

return (
<div className="p-6 max-w-5xl mx-auto space-y-8">
{/* Select Wallet */}
<div>
<h2 className="text-lg font-semibold mb-4">Select Wallet</h2>
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
{wallets.map((wallet) => (
<button
key={wallet.id}
onClick={() => setSelectedWallet(wallet.id)}
className={`border rounded-xl p-4 text-left transition ${
selectedWallet === wallet.id
? "border-blue-600 shadow-lg"
: "border-gray-200"
}`}
>
<div className={`w-10 h-10 ${wallet.color} rounded-lg mb-3`} />
<h3 className="font-medium">{wallet.name}</h3>
<p className="text-sm text-gray-500">{wallet.balance}</p>
</button>
))}
</div>
</div>

{/* Recent Contacts */}
<div>
<h2 className="text-lg font-semibold mb-4">Recent Contacts</h2>
<div className="flex gap-4 overflow-x-auto pb-2">
{recentContacts.map((contact) => (
  <button
    key={contact.phone}
    type="button"
    onClick={() => setForm(f => ({ ...f, phone: contact.phone, name: contact.name }))}
    className="flex flex-col items-center focus:outline-none"
    title="Fill with this contact"
  >
    <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center text-sm font-medium">
      {contact.initials}
    </div>
    <p className="text-xs mt-2">{contact.name}</p>
  </button>
))} 
</div>
</div>

{/* Request Money Form */}
<div className="bg-white p-6 rounded-xl shadow-md">
<h2 className="text-lg font-semibold mb-4">Request Money</h2>
<form className="space-y-4" onSubmit={e => {
  e.preventDefault();
  // Validation
  const newErrors: any = {};
  if (!selectedWallet) newErrors.wallet = 'Select a wallet';
  if (!form.phone || !/^0\d{9}$/.test(form.phone)) newErrors.phone = 'Valid phone required';
  if (!form.name) newErrors.name = 'Name required';
  if (!form.amount || isNaN(Number(form.amount)) || Number(form.amount) <= 0) newErrors.amount = 'Enter a valid amount';
  setErrors(newErrors);
  if (Object.keys(newErrors).length === 0) {
    setSuccess(true);
    setTimeout(() => setSuccess(false), 2000);
    setForm({ phone: '', name: '', amount: '', message: '' });
    setSelectedWallet(null);
  }
}}>
  {errors.wallet && <div className="text-red-500 text-xs mb-2">{errors.wallet}</div>}
  <div>
    <label className="block text-sm font-medium mb-1">Recipient Phone Number</label>
    <input
      type="tel"
      value={form.phone}
      onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
      placeholder="0XX XXX XXXX"
      className="w-full border rounded-lg px-4 py-2"
    />
    {errors.phone && <div className="text-red-500 text-xs mt-1">{errors.phone}</div>}
  </div>
  <div>
    <label className="block text-sm font-medium mb-1">Recipient Name</label>
    <input
      type="text"
      value={form.name}
      onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
      placeholder="Enter recipient name"
      className="w-full border rounded-lg px-4 py-2"
    />
    {errors.name && <div className="text-red-500 text-xs mt-1">{errors.name}</div>}
  </div>
  <div>
    <label className="block text-sm font-medium mb-1">Amount</label>
    <input
      type="number"
      step="0.01"
      value={form.amount}
      onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
      placeholder="₵0.00"
      className="w-full border rounded-lg px-4 py-2"
    />
    {errors.amount && <div className="text-red-500 text-xs mt-1">{errors.amount}</div>}
  </div>
  <div>
    <label className="block text-sm font-medium mb-1">Message (Optional)</label>
    <textarea
      value={form.message}
      onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
      placeholder="Add a note for the recipient..."
      className="w-full border rounded-lg px-4 py-2"
    ></textarea>
  </div>
  <button
    type="submit"
    className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
    disabled={!selectedWallet || !form.phone || !form.name || !form.amount || Object.keys(errors).length > 0}
  >
    Continue
  </button>
  {success && <div className="text-green-600 text-center mt-3">Request sent successfully!</div>}
</form>
</div>
</div>
);
}
