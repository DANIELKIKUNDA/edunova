import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/di/providers.dart';

final _verifiedOfflineUriProvider = FutureProvider.family<String?, String>((ref, id) async {
  return ref.read(offlineResourceStoreProvider).finalUri(id);
});

class OfflineStoragePage extends ConsumerWidget {
  const OfflineStoragePage({super.key});
  String _fmt(int bytes){
    const units=['o','Ko','Mo','Go']; var n=bytes.toDouble(); var i=0; while(n>=1024&&i<units.length-1){n/=1024;i++;} return '${n.toStringAsFixed(i==0?0:1)} ${units[i]}';
  }
  @override Widget build(BuildContext context,WidgetRef ref){
    final all=ref.watch(offlineResourcesProvider);
    final policy=ref.watch(contentCachePolicyProvider);
    return Scaffold(appBar:AppBar(title:const Text('Contenus hors connexion')),body:ListView(padding:const EdgeInsets.fromLTRB(18,12,18,120),children:[
      policy.when(loading:()=>const LinearProgressIndicator(),error:(e,_)=>Text('$e'),data:(p)=>Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        const Text('Politique de stockage',style:TextStyle(fontWeight:FontWeight.w900,fontSize:17)),const SizedBox(height:8),
        Text('Cache EduNova maximal : ${_fmt(p.maxCacheBytes)}'),Text('Réserve cible d’espace libre : ${_fmt(p.minFreeBytes)}'),
        Text(p.wifiOnlyLargeDownloads?'Gros téléchargements : Wi‑Fi uniquement':'Gros téléchargements : tous réseaux'),
        const SizedBox(height:6),const Text('Les documents personnels ne sont jamais supprimés automatiquement.',style:TextStyle(fontSize:12)),
      ])))),
      const SizedBox(height:12),
      all.when(loading:()=>const LinearProgressIndicator(),error:(e,_)=>Text('$e'),data:(items){
        final used=items.where((e)=>e.ready).fold<int>(0,(a,b)=>a+(b.totalBytes??0));
        final active=items.where((e)=>e.state=='downloading').length;
        return Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Card(child:ListTile(leading:const Icon(Icons.storage_rounded),title:Text('${_fmt(used)} utilisés'),subtitle:Text('$active téléchargement(s) actif(s) · ${items.where((e)=>e.ready).length} ressource(s) prêtes'),trailing:TextButton(onPressed:()async{
            try{
              final removed=await ref.read(runCacheCleanupProvider).call();
              ref.invalidate(offlineResourcesProvider);
              if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(removed==0?'Aucun nettoyage nécessaire':'${_fmt(removed)} libérés')));
            }catch(e){if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Nettoyage impossible : $e')));}
          },child:const Text('Optimiser')))),
          const SizedBox(height:12),
          Text('Ressources',style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:8),
          if(items.isEmpty)const Card(child:ListTile(leading:Icon(Icons.download_done_outlined),title:Text('Aucun contenu téléchargé'),subtitle:Text('Depuis un cours EduNova, utilisez le bouton hors connexion.'))),
          ...items.map((s)=>Card(child:FutureBuilder<String?>(
            future: s.ready ? ref.watch(_verifiedOfflineUriProvider(s.resourceId).future) : null,
            builder: (context, fileSnapshot) {
              final verified = s.ready && fileSnapshot.hasData &&
                  fileSnapshot.data != null && fileSnapshot.data == s.localUri;
              final missing = s.ready && fileSnapshot.connectionState == ConnectionState.done && !verified;
              return ListTile(
            leading:Icon(missing?Icons.warning_amber_rounded:verified?Icons.offline_pin_rounded:s.state=='failed'?Icons.error_outline:Icons.downloading_rounded),
            title:Text(s.resourceId,maxLines:1,overflow:TextOverflow.ellipsis),
            subtitle:Text(missing?'Fichier local introuvable ou inaccessible : télécharger à nouveau':verified?'Disponible hors connexion · ${_fmt(s.totalBytes??0)}':s.ready?'Vérification du fichier local…':s.state=='failed'?(s.lastError??'Échec'):'${(s.progress*100).round()} %'),
            trailing:Wrap(spacing:2,children:[IconButton(onPressed:()async{
              try{await ref.read(offlineDeliveryRepositoryProvider).setPinned(s.resourceId,!s.pinned);ref.invalidate(offlineResourcesProvider);}
              catch(e){if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Modification impossible : $e')));}
            },icon:Icon(s.pinned?Icons.push_pin:Icons.push_pin_outlined),tooltip:'Épingler'),IconButton(onPressed:()async{
              final confirmed=await showDialog<bool>(context:context,builder:(dialogContext)=>AlertDialog(
                title:const Text('Supprimer le téléchargement ?'),
                content:Text(s.pinned?'Cette ressource est épinglée. Sa copie hors connexion sera supprimée.':'La copie hors connexion sera supprimée. Vous pourrez la télécharger à nouveau.'),
                actions:[TextButton(onPressed:()=>Navigator.pop(dialogContext,false),child:const Text('Annuler')),
                  FilledButton(onPressed:()=>Navigator.pop(dialogContext,true),child:const Text('Supprimer'))],
              ));
              if(confirmed!=true||!context.mounted)return;
              try{
                await ref.read(offlineResourceStoreProvider).delete(s.resourceId);
                await ref.read(offlineDeliveryRepositoryProvider).reset(s.resourceId);
                ref.invalidate(offlineResourcesProvider);
                ref.invalidate(_verifiedOfflineUriProvider(s.resourceId));
                if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Copie hors connexion supprimée')));
              }catch(e){if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Suppression impossible : $e')));}
            },icon:const Icon(Icons.delete_outline),tooltip:'Supprimer')]),
            );
            },
          ))),
        ]);
      }),
    ]));
  }
}
