import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../../core/di/providers.dart';

/// Payment is confirmed exclusively by the server's verified provider webhook.
/// The UI never activates a licence from a client-side success message.
class CampusPaidCheckoutDialog extends ConsumerStatefulWidget {
  const CampusPaidCheckoutDialog({super.key, required this.institutionId});
  final String institutionId;
  @override
  ConsumerState<CampusPaidCheckoutDialog> createState() => _CampusPaidCheckoutDialogState();
}

class _CampusPaidCheckoutDialogState extends ConsumerState<CampusPaidCheckoutDialog> {
  final phone = TextEditingController();
  final key = const Uuid().v4();
  bool busy = false;
  String? message;
  String? orderId;
  String? selectedOfferCode;
  List<Map<String, dynamic>> availableOffers = [];
  @override
  void dispose() { phone.dispose(); super.dispose(); }

  Future<Map<String, dynamic>> _request(String method, String path, [Map<String, dynamic>? data]) async {
    final identity = ref.read(identityRepositoryProvider);
    var session = await identity.currentSession();
    if (session == null) throw StateError('Connexion nécessaire');
    if (session.accessExpired) session = await identity.refresh();
    final options = <String, dynamic>{'Authorization':'Bearer ${session.accessToken}', 'Idempotency-Key':key};
    final dio = ref.read(apiClientProvider).dio;
    final response = method == 'POST'
        ? await dio.post(path, data:data, options: _options(options))
        : await dio.get(path, options:_options(options));
    return Map<String, dynamic>.from(response.data as Map);
  }

  dynamic _options(Map<String, dynamic> headers) {
    // Dio Options is built here to ensure the bearer token never enters logs.
    return Options(headers: headers);
  }

  Future<void> _start() async {
    setState(() {busy=true; message=null;});
    try {
      final offers = await _loadOffers();
      if (offers.isEmpty) throw StateError('Aucune offre Campus payante disponible.');
      final offer = offers.where((o) => o['code'] == selectedOfferCode).firstOrNull;
      if (offer == null) throw StateError('Sélectionnez une offre Campus.');
      final result = await _request('POST','/v1/commerce/campus/${Uri.encodeComponent(widget.institutionId)}/paid-checkout',{
        'offer_code':offer['code'], 'phone_number':phone.text.trim(), 'provider':'sandbox-mobile-money',
      });
      if (!mounted) return;
      setState(() {orderId=result['order_id']?.toString(); message='Demande envoyée (${result['amount_cdf']} FC). Confirmez sur votre téléphone, puis vérifiez le statut.';});
    } catch (_) {
      if (mounted) setState(() => message='Impossible de lancer le paiement. Vérifiez le numéro, votre rôle et la disponibilité du service.');
    } finally {if (mounted) setState(() => busy=false);}
  }

  Future<List<Map<String, dynamic>>> _loadOffers() async {
    final response = await ref.read(apiClientProvider).dio.get('/v1/commerce/campus/public-offers');
    return (response.data as List).map((e)=>Map<String,dynamic>.from(e as Map)).toList();
  }

  Future<void> _refresh() async {
    if (orderId==null) return;
    setState(()=>busy=true);
    try {
      final result=await _request('GET','/v1/commerce/campus/${Uri.encodeComponent(widget.institutionId)}/paid-orders/${Uri.encodeComponent(orderId!)}');
      if (mounted) setState(()=>message='Statut serveur : ${result['status']}. ${result['license_id'] == null ? 'Licence non activée.' : 'Licence activée.'}');
    } catch (_) {if (mounted) setState(()=>message='Vérification impossible. Réessayez sans refaire le paiement.');}
    finally {if(mounted) setState(()=>busy=false);}
  }

  @override
  void initState() { super.initState(); Future.microtask(() async { try { final rows = await _loadOffers(); if (mounted) setState(() => availableOffers = rows); } catch (_) { if (mounted) setState(() => message = 'Catalogue des offres indisponible.'); } }); }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title:const Text('Renouvellement Campus'),
    content:Column(mainAxisSize:MainAxisSize.min,children:[
      const Text('Le paiement est confirmé par le serveur, jamais par cette fenêtre.'),
      DropdownButtonFormField<String>(value: selectedOfferCode, isExpanded: true, decoration: const InputDecoration(labelText:'Offre Campus'), items: availableOffers.map((offer) => DropdownMenuItem<String>(value: offer['code'].toString(), child: Text("${offer['label']} · ${offer['price_cdf']} FC · ${offer['seats']} places / ${offer['duration_days']} j", overflow: TextOverflow.ellipsis))).toList(), onChanged: busy || orderId != null ? null : (value) => setState(() => selectedOfferCode = value)),
      TextField(controller:phone,keyboardType:TextInputType.phone,decoration:const InputDecoration(labelText:'Numéro Mobile Money')),
      if(message!=null) Padding(padding:const EdgeInsets.only(top:12),child:Text(message!)),
    ]),
    actions:[TextButton(onPressed:()=>Navigator.pop(context),child:const Text('Fermer')),
      if(orderId!=null) TextButton(onPressed:busy?null:_refresh,child:const Text('Vérifier')),
      FilledButton(onPressed:busy||orderId!=null||selectedOfferCode==null?null:_start,child:const Text('Payer'))],
  );
}
