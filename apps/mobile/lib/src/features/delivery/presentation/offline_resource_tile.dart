import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/di/providers.dart';
import '../../library/domain/library.dart';

class OfflineResourceTile extends ConsumerStatefulWidget {
  const OfflineResourceTile({super.key,required this.courseId,required this.resource});
  final String courseId;
  final LibraryResourceView resource;
  @override ConsumerState<OfflineResourceTile> createState()=>_OfflineResourceTileState();
}
class _OfflineResourceTileState extends ConsumerState<OfflineResourceTile>{
  bool busy=false;
  Future<void> _download() async{
    if(busy)return; setState(()=>busy=true);
    try{
      // Refresh manifest immediately before granting delivery: capability tokens are intentionally short-lived.
      await ref.read(offlineDeliveryRepositoryProvider).enqueue(courseId:widget.courseId,resourceId:widget.resource.id,priority:80);
      final done=await ref.read(runDownloadQueueProvider).drain(limit:1);
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(done>0?'Ressource prête hors ligne.':'Téléchargement mis en attente.')));
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Téléchargement impossible : $e')));}
    finally{if(mounted)setState(()=>busy=false);}
  }
  Future<void> _togglePin(bool currentlyPinned) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      await ref.read(offlineDeliveryRepositoryProvider).setPinned(widget.resource.id, !currentlyPinned);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Impossible de modifier l’épinglage hors connexion. Réessaie.')));
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }
  @override Widget build(BuildContext context){
    final state=ref.watch(offlineResourceStateProvider(widget.resource.id));
    return state.when(
      loading:()=>const SizedBox(width:24,height:24,child:CircularProgressIndicator(strokeWidth:2)),
      error:(e,_)=>IconButton(onPressed:_download,icon:const Icon(Icons.cloud_download_outlined),tooltip:'Réessayer'),
      data:(s){
        final ready=s?.ready==true;
        if(ready){return Row(mainAxisSize:MainAxisSize.min,children:[const Icon(Icons.offline_pin_rounded),IconButton(onPressed:busy?null:()=>_togglePin(s?.pinned??false),icon:Icon((s?.pinned??false)?Icons.push_pin:Icons.push_pin_outlined),tooltip:'Épingler')]);}
        if(s?.state=='downloading'){return SizedBox(width:38,height:38,child:Stack(alignment:Alignment.center,children:[CircularProgressIndicator(value:s!.progress),Text('${(s.progress*100).round()}',style:const TextStyle(fontSize:10,fontWeight:FontWeight.w800))]));}
        return IconButton(onPressed:(widget.resource.offlineAllowed&&widget.resource.access=='available'&&!busy)?_download:null,icon:busy?const SizedBox(width:20,height:20,child:CircularProgressIndicator(strokeWidth:2)):Icon(widget.resource.access=='locked'?Icons.lock_rounded:Icons.download_for_offline_outlined),tooltip:widget.resource.access=='locked'?'Premium requis':'Rendre disponible hors ligne');
      },
    );
  }
}
