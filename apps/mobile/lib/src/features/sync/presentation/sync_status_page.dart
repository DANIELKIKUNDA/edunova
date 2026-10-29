import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/di/providers.dart';

class SyncStatusPage extends ConsumerStatefulWidget {
  const SyncStatusPage({super.key});
  @override ConsumerState<SyncStatusPage> createState()=>_SyncStatusPageState();
}

class _SyncStatusPageState extends ConsumerState<SyncStatusPage>{
  bool busy=false;
  String? message;

  Future<void> _sync() async{
    if(busy)return;
    setState(()=>busy=true);
    try{
      final result=await ref.read(runCloudSyncProvider)();
      if(!mounted)return;
      ref.invalidate(syncDevicesProvider);
      ref.invalidate(cloudSyncStateProvider);
      ref.invalidate(syncDiagnosticsProvider);
      ref.invalidate(syncConflictsProvider);
      setState(()=>message='${result.pushed} envoyés · ${result.pulled} reçus · ${result.conflicts} conflits');
    }catch(e){if(mounted)setState(()=>message='Synchronisation impossible : $e');}
    finally{if(mounted)setState(()=>busy=false);}
  }

  Future<String?> _accountId() async => (await ref.read(identityRepositoryProvider).currentSession())?.accountId;

  @override Widget build(BuildContext context){
    final state=ref.watch(cloudSyncStateProvider);
    final conflicts=ref.watch(syncConflictsProvider);
    final devices=ref.watch(syncDevicesProvider);
    final diagnostics=ref.watch(syncDiagnosticsProvider);
    return Scaffold(appBar:AppBar(title:const Text('Synchronisation')),body:ListView(padding:const EdgeInsets.all(18),children:[
      Card(child:Padding(padding:const EdgeInsets.all(18),child:state.when(
        loading:()=>const LinearProgressIndicator(),error:(e,_)=>Text('$e'),data:(s)=>Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          const Row(children:[Icon(Icons.cloud_done_rounded),SizedBox(width:10),Text('Cloud EduNova',style:TextStyle(fontWeight:FontWeight.w900,fontSize:18))]),
          const SizedBox(height:10),
          Text(s==null?'Connecte-toi pour synchroniser':'Appareil protégé · ${s.registered?'enregistré':'à enregistrer'}'),
          if(s?.lastSyncAt!=null) Text('Dernière synchronisation : ${s!.lastSyncAt!.toLocal()}'),
          if(s?.lastBootstrapAt!=null) Text('Dernière reconstruction cloud : ${s!.lastBootstrapAt!.toLocal()}',style:Theme.of(context).textTheme.bodySmall),
          if(s?.lastError!=null) Text(s!.lastError!,style:TextStyle(color:Theme.of(context).colorScheme.error)),
          const SizedBox(height:14),FilledButton.icon(onPressed:busy?null:_sync,icon:busy?const SizedBox.square(dimension:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.sync_rounded),label:const Text('Synchroniser maintenant')),
          if(message!=null)...[const SizedBox(height:8),Text(message!)],
          const SizedBox(height:12),const Divider(),const SizedBox(height:8),
          const Row(crossAxisAlignment:CrossAxisAlignment.start,children:[Icon(Icons.shield_outlined,size:20),SizedBox(width:8),Expanded(child:Text('Tes PDF, photos, OCR, chunks et conversations personnelles restent sur cet appareil. Seules les données légères autorisées passent par le cloud.'))]),
        ]),
      ))),
      const SizedBox(height:16),
      Text('Santé de la synchronisation',style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:8),
      diagnostics.when(
        loading:()=>const LinearProgressIndicator(),
        error:(e,_)=>Card(child:ListTile(leading:const Icon(Icons.warning_amber_rounded),title:const Text('Diagnostic indisponible'),subtitle:Text('$e'))),
        data:(d)=>Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Row(children:[Icon(d.healthy?Icons.verified_rounded:Icons.health_and_safety_outlined),const SizedBox(width:10),Text(d.healthy?'Synchronisation saine':'Attention requise',style:const TextStyle(fontWeight:FontWeight.w900,fontSize:16))]),
          const SizedBox(height:10),
          Wrap(spacing:8,runSpacing:8,children:[
            Chip(label:Text('${d.pending} en attente')),
            Chip(label:Text('${d.openConflicts} conflit${d.openConflicts>1?'s':''}')),
            Chip(label:Text('${d.deadLetters} rejet${d.deadLetters>1?'s':''}')),
          ]),
          if(d.oldestPendingAt!=null) Padding(padding:const EdgeInsets.only(top:8),child:Text('Plus ancienne modification non envoyée : ${d.oldestPendingAt!.toLocal()}')),
        ]))),
      ),
      const SizedBox(height:16),
      Text('Mes appareils',style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:8),
      devices.when(
        loading:()=>const LinearProgressIndicator(),error:(e,_)=>Card(child:ListTile(title:const Text('Appareils indisponibles'),subtitle:Text('$e'))),
        data:(items)=>items.isEmpty?const Card(child:ListTile(leading:Icon(Icons.devices_rounded),title:Text('Aucun appareil cloud enregistré'))):Column(children:items.map((d)=>Card(child:ListTile(
          leading:Icon(d.active?Icons.devices_rounded:Icons.block_rounded),
          title:Text(d.name,style:const TextStyle(fontWeight:FontWeight.w800)),
          subtitle:Text('${d.platform} · ${d.appVersion}${d.lastSyncAt==null?'':' · sync ${d.lastSyncAt!.toLocal()}'}'),
          trailing:d.active?IconButton(tooltip:'Révoquer cet appareil',icon:const Icon(Icons.phonelink_erase_rounded),onPressed:busy?null:()async{
            final current=state.asData?.value?.deviceId;
            if(current==d.deviceId){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Utilise la sécurité du compte pour déconnecter cet appareil actif.')));return;}
            if(busy)return;
            setState(()=>busy=true);
            try{
              await ref.read(cloudSyncRemoteGatewayProvider).revokeDevice(d.deviceId);
              ref.invalidate(syncDevicesProvider);
              if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Appareil révoqué.')));
            }catch(e){
              if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Révocation impossible : $e')));
            }finally{
              if(mounted)setState(()=>busy=false);
            }
          }):const Chip(label:Text('Révoqué')),
        ))).toList()),
      ),
      const SizedBox(height:16),
      Text('Conflits à vérifier',style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:8),
      conflicts.when(loading:()=>const LinearProgressIndicator(),error:(e,_)=>Text('$e'),data:(items)=>items.isEmpty?const Card(child:ListTile(leading:Icon(Icons.check_circle_outline_rounded),title:Text('Aucun conflit'))):Column(children:items.map((c)=>Card(child:ListTile(
        leading:const Icon(Icons.merge_type_rounded),title:Text(c.entityType),subtitle:Text('${c.reason} · ${c.entityId}'),
        trailing:PopupMenuButton<String>(onSelected:(v)async{
          if(busy)return;
          final accountId=await _accountId();
          if(!mounted||accountId==null)return;
          setState(()=>busy=true);
          try{
            await ref.read(cloudSyncLocalRepositoryProvider).resolveConflict(accountId,c.id,keepLocal:v=='local');
            ref.invalidate(syncConflictsProvider);
            ref.invalidate(syncDiagnosticsProvider);
            if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conflit résolu. Synchronisez pour transmettre les changements.')));
          }catch(e){
            if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Résolution impossible : $e')));
          }finally{if(mounted)setState(()=>busy=false);}
        },itemBuilder:(_)=>const [PopupMenuItem(value:'cloud',child:Text('Garder la version cloud')),PopupMenuItem(value:'local',child:Text('Garder cet appareil'))]),
      ))).toList())),
    ]));
  }
}
